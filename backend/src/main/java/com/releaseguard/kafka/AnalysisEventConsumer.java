package com.releaseguard.kafka;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import com.releaseguard.service.ProcessedEventService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class AnalysisEventConsumer {

    private static final Logger log =
        LoggerFactory.getLogger(AnalysisEventConsumer.class);

    private final AnalysisService analysisService;
    private final ProcessedEventService processedEventService;
    private final com.releaseguard.redis.RedisIdempotencyService redisIdempotencyService;

    public AnalysisEventConsumer(
        AnalysisService analysisService,
        ProcessedEventService processedEventService,
        com.releaseguard.redis.RedisIdempotencyService redisIdempotencyService
    ) {
        this.analysisService = analysisService;
        this.processedEventService = processedEventService;
        this.redisIdempotencyService = redisIdempotencyService;
    }

    @KafkaListener(
        topics = KafkaTopics.ANALYSIS_REQUEST,
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consume(
        EventEnvelope<AnalyzePullRequestEvent> event
    ) {

        String eventId = event.getEventId();

        String correlationId =
            event.getCorrelationId();

        try {

            MDC.put(
                "eventId",
                eventId
            );

            MDC.put(
                "correlationId",
                correlationId
            );

            log.info(
                "Received analysis event: eventId={}, correlationId={}",
                eventId,
                correlationId
            );

            // Step 1: Redis Fast Idempotency Check & Atomic Distributed Lease
            com.releaseguard.redis.RedisIdempotencyService.LeaseResult leaseResult =
                redisIdempotencyService.acquireProcessingLease(eventId);

            if (leaseResult.status() == com.releaseguard.redis.RedisIdempotencyService.LeaseStatus.ALREADY_COMPLETED) {
                log.info(
                    "Ignoring already completed event in Redis: eventId={}, correlationId={}",
                    eventId,
                    correlationId
                );
                return;
            }

            if (leaseResult.status() == com.releaseguard.redis.RedisIdempotencyService.LeaseStatus.IN_PROGRESS) {
                log.warn(
                    "Event is currently being processed by another worker in Redis: eventId={}, correlationId={}",
                    eventId,
                    correlationId
                );
                throw new EventProcessingInProgressException(
                    "Event is currently being processed by another worker: " + eventId
                );
            }

            // Step 2: Authoritative PostgreSQL check (Defense in depth / fail-open fallback)
            if (processedEventService.isCompleted(eventId)) {
                log.info(
                    "Ignoring already completed event in PostgreSQL: eventId={}, correlationId={}",
                    eventId,
                    correlationId
                );
                redisIdempotencyService.markCompleted(eventId);
                return;
            }

            processedEventService.markProcessing(
                eventId,
                event.getEventType(),
                correlationId
            );

            AnalyzePullRequestEvent payload =
                event.getPayload();

            try {
                analysisService.analyzePullRequest(
                    payload.getProjectId(),
                    payload.getOwner(),
                    payload.getRepository(),
                    payload.getPullRequestNumber()
                );
            } catch (Exception ex) {
                // If processing fails, release Redis lease using worker's specific token
                redisIdempotencyService.releaseProcessingLease(eventId, leaseResult.leaseToken());
                throw ex;
            }

            // Step 3: Mark completed in both PostgreSQL (authoritative) and Redis (fast cache)
            processedEventService.markCompleted(
                eventId
            );
            redisIdempotencyService.markCompleted(
                eventId,
                leaseResult.leaseToken()
            );

            log.info(
                "Analysis event completed: eventId={}, correlationId={}",
                eventId,
                correlationId
            );

        } finally {

            MDC.remove("eventId");
            MDC.remove("correlationId");
        }
    }
}
