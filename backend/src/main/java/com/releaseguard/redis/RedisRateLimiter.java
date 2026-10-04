package com.releaseguard.redis;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Redis fixed-window rate limiter.
 * Tracks requests per minute using an atomic INCR with a 60-second expiration.
 * Fails open if Redis is down or if rate limiting is disabled.
 */
@Service
public class RedisRateLimiter {

    private static final Logger log =
            LoggerFactory.getLogger(RedisRateLimiter.class);

    private final StringRedisTemplate redisTemplate;
    private final RedisProperties properties;

    @Autowired
    @SuppressWarnings("deprecation")
    public RedisRateLimiter(
            @org.springframework.lang.Nullable StringRedisTemplate redisTemplate,
            RedisProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.properties = properties;
    }

    public boolean tryAcquire(String actionKey) {
        return tryAcquire(actionKey, properties.getRateLimiter().getRequestsPerMinute());
    }

    public boolean tryAcquire(String actionKey, int maxRequestsPerMinute) {
        if (!properties.isEnabled()
                || !properties.getRateLimiter().isEnabled()
                || redisTemplate == null) {
            return true;
        }

        String rateLimitKey = RedisKeys.rateLimit(actionKey);
        try {
            Long count = redisTemplate.opsForValue().increment(rateLimitKey);
            if (count != null && count == 1L) {
                redisTemplate.expire(rateLimitKey, Duration.ofMinutes(1));
            }
            return count != null && count <= maxRequestsPerMinute;
        } catch (Exception ex) {
            log.warn("Redis rate limiter error for key={}. Failing open. Error: {}",
                    actionKey, ex.getMessage());
            return true;
        }
    }
}
