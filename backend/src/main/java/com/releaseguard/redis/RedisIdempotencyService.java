package com.releaseguard.redis;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Collections;
import java.util.UUID;

@Service
@SuppressWarnings("deprecation")
public class RedisIdempotencyService {

    private static final Logger log =
            LoggerFactory.getLogger(RedisIdempotencyService.class);

    public static final String STATUS_PROCESSING_PREFIX = "PROCESSING:";
    public static final String STATUS_COMPLETED = "COMPLETED";

    private static final RedisScript<Long> RELEASE_LEASE_SCRIPT = new DefaultRedisScript<>(
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else " +
            "    return 0 " +
            "end",
            Long.class
    );

    private static final RedisScript<Long> MARK_COMPLETED_SCRIPT = new DefaultRedisScript<>(
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    redis.call('set', KEYS[1], 'COMPLETED', 'EX', ARGV[2]) " +
            "    return 1 " +
            "else " +
            "    return 0 " +
            "end",
            Long.class
    );

    public enum LeaseStatus {
        ACQUIRED,
        ALREADY_COMPLETED,
        IN_PROGRESS,
        FALLBACK
    }

    public record LeaseResult(LeaseStatus status, @Nullable String leaseToken) {
        public boolean isAcquired() {
            return status == LeaseStatus.ACQUIRED;
        }
    }

    private final StringRedisTemplate redisTemplate;
    private final RedisProperties properties;

    @Autowired
    public RedisIdempotencyService(
            @Nullable StringRedisTemplate redisTemplate,
            RedisProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.properties = properties;
    }

    public LeaseResult acquireProcessingLease(String eventId) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return new LeaseResult(LeaseStatus.FALLBACK, null);
        }

        String key = RedisKeys.idempotency(eventId);
        long processingTtlSeconds =
                properties.getTtls().getIdempotencyProcessingSeconds();
        String leaseToken = UUID.randomUUID().toString();
        String leaseValue = STATUS_PROCESSING_PREFIX + leaseToken;

        try {
            Boolean acquired = redisTemplate.opsForValue()
                    .setIfAbsent(key, leaseValue, Duration.ofSeconds(processingTtlSeconds));

            if (Boolean.TRUE.equals(acquired)) {
                return new LeaseResult(LeaseStatus.ACQUIRED, leaseToken);
            }

            String currentStatus = redisTemplate.opsForValue().get(key);
            if (currentStatus != null && currentStatus.startsWith(STATUS_COMPLETED)) {
                return new LeaseResult(LeaseStatus.ALREADY_COMPLETED, null);
            }

            return new LeaseResult(LeaseStatus.IN_PROGRESS, null);

        } catch (Exception ex) {
            log.warn("Redis error during acquireProcessingLease for eventId={}. Falling back to PostgreSQL. Error: {}",
                    eventId, ex.getMessage());
            return new LeaseResult(LeaseStatus.FALLBACK, null);
        }
    }

    public boolean markCompleted(String eventId, @Nullable String leaseToken) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return false;
        }

        String key = RedisKeys.idempotency(eventId);
        long completedTtlSeconds =
                properties.getTtls().getIdempotencyCompletedSeconds();

        try {
            if (leaseToken != null) {
                // Atomic transition: only overwrite if current value matches my lease token
                Long executed = redisTemplate.execute(
                        MARK_COMPLETED_SCRIPT,
                        Collections.singletonList(key),
                        STATUS_PROCESSING_PREFIX + leaseToken,
                        String.valueOf(completedTtlSeconds)
                );
                return Long.valueOf(1L).equals(executed);
            }

            // Fallback for direct synchronization (e.g. sync from PostgreSQL)
            redisTemplate.opsForValue()
                    .set(key, STATUS_COMPLETED, Duration.ofSeconds(completedTtlSeconds));
            return true;

        } catch (Exception ex) {
            log.warn("Redis error during markCompleted for eventId={}. Error: {}",
                    eventId, ex.getMessage());
            return false;
        }
    }

    public boolean markCompleted(String eventId) {
        return markCompleted(eventId, null);
    }

    public boolean releaseProcessingLease(String eventId, @Nullable String leaseToken) {
        if (!properties.isEnabled() || redisTemplate == null || leaseToken == null) {
            return false;
        }

        String key = RedisKeys.idempotency(eventId);

        try {
            // Atomic release: only delete if current value equals my lease token
            Long result = redisTemplate.execute(
                    RELEASE_LEASE_SCRIPT,
                    Collections.singletonList(key),
                    STATUS_PROCESSING_PREFIX + leaseToken
            );
            return Long.valueOf(1L).equals(result);

        } catch (Exception ex) {
            log.warn("Redis error during releaseProcessingLease for eventId={}. Error: {}",
                    eventId, ex.getMessage());
            return false;
        }
    }

    public boolean isCompleted(String eventId) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return false;
        }

        String key = RedisKeys.idempotency(eventId);
        try {
            String status = redisTemplate.opsForValue().get(key);
            return status != null && status.startsWith(STATUS_COMPLETED);
        } catch (Exception ex) {
            log.warn("Redis error during isCompleted check for eventId={}. Error: {}",
                    eventId, ex.getMessage());
            return false;
        }
    }
}
