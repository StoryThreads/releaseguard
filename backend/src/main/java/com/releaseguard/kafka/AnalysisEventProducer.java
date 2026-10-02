package com.releaseguard.kafka;

import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import com.releaseguard.event.EventType;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.UUID;

@Component
public class AnalysisEventProducer {

    private final KafkaTemplate<
        String,
        EventEnvelope<AnalyzePullRequestEvent>
        > kafkaTemplate;

    public AnalysisEventProducer(
        KafkaTemplate<
            String,
            EventEnvelope<AnalyzePullRequestEvent>
            > kafkaTemplate
    ) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publishAnalysisRequest(
        Long projectId,
        String owner,
        String repository,
        Long pullRequestNumber,
        String correlationId
    ) {

        AnalyzePullRequestEvent payload =
            new AnalyzePullRequestEvent(
                projectId,
                owner,
                repository,
                pullRequestNumber
            );

        EventEnvelope<AnalyzePullRequestEvent> envelope =
            new EventEnvelope<>(
                UUID.randomUUID().toString(),
                EventType.ANALYZE_PULL_REQUEST.name(),
                Instant.now(),
                correlationId,
                payload
            );

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            envelope.getEventId(),
            envelope
        );
    }
}
