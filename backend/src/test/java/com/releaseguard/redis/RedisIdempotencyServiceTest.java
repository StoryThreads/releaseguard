package com.releaseguard.redis;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.core.script.RedisScript;

import java.time.Duration;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.startsWith;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@SuppressWarnings("unchecked")
class RedisIdempotencyServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOperations;

    private RedisProperties properties;
    private RedisIdempotencyService idempotencyService;

    @BeforeEach
    void setUp() {
        properties = new RedisProperties();
        properties.setEnabled(true);
        properties.getTtls().setIdempotencyProcessingSeconds(300L);
        properties.getTtls().setIdempotencyCompletedSeconds(86400L);

        idempotencyService = new RedisIdempotencyService(redisTemplate, properties);
    }

    @Test
    void shouldAcquireLeaseWithUniqueTokenWhenKeyAbsent() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.setIfAbsent(
                eq("idemp:event:evt-1"),
                startsWith(RedisIdempotencyService.STATUS_PROCESSING_PREFIX),
                eq(Duration.ofSeconds(300L))
        )).thenReturn(Boolean.TRUE);

        RedisIdempotencyService.LeaseResult result =
                idempotencyService.acquireProcessingLease("evt-1");

        assertEquals(RedisIdempotencyService.LeaseStatus.ACQUIRED, result.status());
        assertTrue(result.isAcquired());
        assertNotNull(result.leaseToken());
    }

    @Test
    void shouldDetectAlreadyCompletedEvent() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.setIfAbsent(
                eq("idemp:event:evt-1"),
                startsWith(RedisIdempotencyService.STATUS_PROCESSING_PREFIX),
                eq(Duration.ofSeconds(300L))
        )).thenReturn(Boolean.FALSE);
        when(valueOperations.get("idemp:event:evt-1"))
                .thenReturn(RedisIdempotencyService.STATUS_COMPLETED);

        RedisIdempotencyService.LeaseResult result =
                idempotencyService.acquireProcessingLease("evt-1");

        assertEquals(RedisIdempotencyService.LeaseStatus.ALREADY_COMPLETED, result.status());
        assertFalse(result.isAcquired());
    }

    @Test
    void shouldDetectInProgressEvent() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.setIfAbsent(
                eq("idemp:event:evt-1"),
                startsWith(RedisIdempotencyService.STATUS_PROCESSING_PREFIX),
                eq(Duration.ofSeconds(300L))
        )).thenReturn(Boolean.FALSE);
        when(valueOperations.get("idemp:event:evt-1"))
                .thenReturn("PROCESSING:token-123");

        RedisIdempotencyService.LeaseResult result =
                idempotencyService.acquireProcessingLease("evt-1");

        assertEquals(RedisIdempotencyService.LeaseStatus.IN_PROGRESS, result.status());
        assertFalse(result.isAcquired());
    }

    @Test
    void shouldFailOpenWhenRedisUnavailable() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.setIfAbsent(any(), any(), any(Duration.class)))
                .thenThrow(new RedisConnectionFailureException("Connection refused"));

        RedisIdempotencyService.LeaseResult result =
                idempotencyService.acquireProcessingLease("evt-1");

        assertEquals(RedisIdempotencyService.LeaseStatus.FALLBACK, result.status());
        assertFalse(result.isAcquired());
    }

    @Test
    void shouldFailOpenWhenRedisDisabled() {
        properties.setEnabled(false);

        RedisIdempotencyService.LeaseResult result =
                idempotencyService.acquireProcessingLease("evt-1");

        assertEquals(RedisIdempotencyService.LeaseStatus.FALLBACK, result.status());
        assertFalse(result.isAcquired());
    }

    @Test
    void shouldMarkCompletedWithTokenUsingLuaScript() {
        when(redisTemplate.execute(
                any(RedisScript.class),
                eq(Collections.singletonList("idemp:event:evt-1")),
                eq("PROCESSING:my-token"),
                eq("86400")
        )).thenReturn(1L);

        boolean success = idempotencyService.markCompleted("evt-1", "my-token");

        assertTrue(success);
    }

    @Test
    void shouldFailMarkCompletedIfTokenDoesNotMatch() {
        when(redisTemplate.execute(
                any(RedisScript.class),
                eq(Collections.singletonList("idemp:event:evt-1")),
                eq("PROCESSING:stale-token"),
                eq("86400")
        )).thenReturn(0L);

        boolean success = idempotencyService.markCompleted("evt-1", "stale-token");

        assertFalse(success);
    }

    @Test
    void shouldReleaseProcessingLeaseWithMatchingTokenViaLua() {
        when(redisTemplate.execute(
                any(RedisScript.class),
                eq(Collections.singletonList("idemp:event:evt-1")),
                eq("PROCESSING:worker-a-token")
        )).thenReturn(1L);

        boolean released = idempotencyService.releaseProcessingLease("evt-1", "worker-a-token");

        assertTrue(released);
    }

    @Test
    void shouldNotReleaseProcessingLeaseIfTokenMismatched() {
        // Simulates Worker A trying to release after Worker B reacquired the lease
        when(redisTemplate.execute(
                any(RedisScript.class),
                eq(Collections.singletonList("idemp:event:evt-1")),
                eq("PROCESSING:worker-a-stale-token")
        )).thenReturn(0L);

        boolean released = idempotencyService.releaseProcessingLease("evt-1", "worker-a-stale-token");

        assertFalse(released);
    }

    @Test
    void shouldCheckIsCompleted() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("idemp:event:evt-1"))
                .thenReturn(RedisIdempotencyService.STATUS_COMPLETED);

        assertTrue(idempotencyService.isCompleted("evt-1"));

        when(valueOperations.get("idemp:event:evt-2"))
                .thenReturn("PROCESSING:token-abc");

        assertFalse(idempotencyService.isCompleted("evt-2"));
    }
}
