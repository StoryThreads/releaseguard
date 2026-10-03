package com.releaseguard.redis;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RedisRateLimiterTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOperations;

    private RedisProperties properties;
    private RedisRateLimiter rateLimiter;

    @BeforeEach
    void setUp() {
        properties = new RedisProperties();
        properties.setEnabled(true);
        properties.getRateLimiter().setEnabled(true);
        properties.getRateLimiter().setRequestsPerMinute(5);

        rateLimiter = new RedisRateLimiter(redisTemplate, properties);
    }

    @Test
    void shouldAllowWhenDisabled() {
        properties.getRateLimiter().setEnabled(false);

        boolean allowed = rateLimiter.tryAcquire("github:api");

        assertTrue(allowed);
        verify(redisTemplate, never()).opsForValue();
    }

    @Test
    void shouldAllowFirstRequestAndSetTtl() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment("ratelimit:github:api")).thenReturn(1L);

        boolean allowed = rateLimiter.tryAcquire("github:api");

        assertTrue(allowed);
        verify(redisTemplate).expire(eq("ratelimit:github:api"), eq(Duration.ofMinutes(1)));
    }

    @Test
    void shouldAllowRequestsUnderLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment("ratelimit:github:api")).thenReturn(5L);

        boolean allowed = rateLimiter.tryAcquire("github:api");

        assertTrue(allowed);
    }

    @Test
    void shouldBlockRequestsExceedingLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment("ratelimit:github:api")).thenReturn(6L);

        boolean allowed = rateLimiter.tryAcquire("github:api");

        assertFalse(allowed);
    }

    @Test
    void shouldFailOpenWhenRedisThrows() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment(any()))
                .thenThrow(new RedisConnectionFailureException("Redis timeout"));

        boolean allowed = rateLimiter.tryAcquire("github:api");

        assertTrue(allowed);
    }
}
