package com.releaseguard.kafka;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import com.releaseguard.redis.RedisIdempotencyService;
import com.releaseguard.service.ProcessedEventService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PipelineHardeningTest {

    @Mock
    private AnalysisService analysisService;

    @Mock
    private ProcessedEventService processedEventService;

    @Mock
    private RedisIdempotencyService redisIdempotencyService;

    private AnalysisEventConsumer consumer;

    private static final Long PROJECT_ID = 42L;

    @BeforeEach
    void setUp() {
        consumer = new AnalysisEventConsumer(
                analysisService,
                processedEventService,
                redisIdempotencyService
        );
    }

    private EventEnvelope<AnalyzePullRequestEvent> createEvent(String eventId) {
        return new EventEnvelope<>(
                eventId,
                "ANALYZE_PULL_REQUEST",
                Instant.now(),
                UUID.randomUUID().toString(),
                new AnalyzePullRequestEvent(PROJECT_ID, "StoryThreads", "releaseguard", 10L)
        );
    }

    @Test
    void shouldShortCircuitWhenEventAlreadyCompletedInRedis() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.ALREADY_COMPLETED, null));

        consumer.consume(event);

        verify(analysisService, never()).analyzePullRequest(anyLong(), anyString(), anyString(), anyLong());
        verify(processedEventService, never()).markProcessing(anyString(), anyString(), anyString());
    }

    @Test
    void shouldShortCircuitWhenDuplicateEventCurrentlyInProgressInRedis() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.IN_PROGRESS, null));

        assertThrows(EventProcessingInProgressException.class, () -> consumer.consume(event));

        verify(analysisService, never()).analyzePullRequest(anyLong(), anyString(), anyString(), anyLong());
        verify(processedEventService, never()).markProcessing(anyString(), anyString(), anyString());
    }

    @Test
    void shouldProcessEventSuccessfullyAndMarkCompletedWithLeaseToken() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);
        String token = "lease-token-123";

        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.ACQUIRED, token));
        when(processedEventService.isCompleted(eventId)).thenReturn(false);

        consumer.consume(event);

        verify(processedEventService).markProcessing(eq(eventId), eq("ANALYZE_PULL_REQUEST"), anyString());
        verify(analysisService).analyzePullRequest(PROJECT_ID, "StoryThreads", "releaseguard", 10L);
        verify(processedEventService).markCompleted(eventId);
        verify(redisIdempotencyService).markCompleted(eventId, token);
    }

    @Test
    void shouldReleaseLeaseWithTokenWhenProcessingFailsSoRetryCanProceed() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);
        String token = "lease-token-456";

        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.ACQUIRED, token));
        when(processedEventService.isCompleted(eventId)).thenReturn(false);
        when(analysisService.analyzePullRequest(anyLong(), anyString(), anyString(), anyLong()))
                .thenThrow(new RuntimeException("Simulated transient failure"));

        assertThrows(RuntimeException.class, () -> consumer.consume(event));

        // Must release lease with the worker's specific token so retry can re-acquire without blocking
        verify(redisIdempotencyService).releaseProcessingLease(eventId, token);
        verify(processedEventService, never()).markCompleted(eventId);
        verify(redisIdempotencyService, never()).markCompleted(eq(eventId), anyString());
    }

    @Test
    void shouldFailOpenToPostgresWhenRedisUnavailable() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        // Redis is down or times out -> returns FALLBACK
        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.FALLBACK, null));
        when(processedEventService.isCompleted(eventId)).thenReturn(false);

        consumer.consume(event);

        // Analysis continues via PostgreSQL authoritative check
        verify(processedEventService).markProcessing(eq(eventId), eq("ANALYZE_PULL_REQUEST"), anyString());
        verify(analysisService).analyzePullRequest(PROJECT_ID, "StoryThreads", "releaseguard", 10L);
        verify(processedEventService).markCompleted(eventId);
    }

    @Test
    void shouldSyncCompletedStateToRedisWhenPostgresAlreadyCompleted() {
        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        // Redis key was expired or cleared, but PostgreSQL has record
        when(redisIdempotencyService.acquireProcessingLease(eventId))
                .thenReturn(new RedisIdempotencyService.LeaseResult(RedisIdempotencyService.LeaseStatus.ACQUIRED, "stale-token"));
        when(processedEventService.isCompleted(eventId)).thenReturn(true);

        consumer.consume(event);

        verify(analysisService, never()).analyzePullRequest(anyLong(), anyString(), anyString(), anyLong());
        // Syncs the completed state back to Redis
        verify(redisIdempotencyService).markCompleted(eventId);
    }
}
