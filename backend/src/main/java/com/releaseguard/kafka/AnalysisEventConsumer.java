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

    public AnalysisEventConsumer(
        AnalysisService analysisService,
        ProcessedEventService processedEventService
    ) {
        this.analysisService = analysisService;
        this.processedEventService = processedEventService;
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

            if (
                processedEventService.isCompleted(eventId)
            ) {

                log.info(
                    "Ignoring already completed event: eventId={}, correlationId={}",
                    eventId,
                    correlationId
                );

                return;
            }

            processedEventService.markProcessing(
                eventId,
                event.getEventType(),
                correlationId
            );

            AnalyzePullRequestEvent payload =
                event.getPayload();

            analysisService.analyzePullRequest(
                payload.getOwner(),
                payload.getRepository(),
                payload.getPullRequestNumber()
            );

            processedEventService.markCompleted(
                eventId
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
