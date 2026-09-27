package com.releaseguard.kafka;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.context.EmbeddedKafka;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.time.Instant;
import java.util.UUID;

import static org.mockito.Mockito.timeout;
import static org.mockito.Mockito.verify;

@SpringBootTest
@EmbeddedKafka(
    partitions = 1,
    topics = KafkaTopics.ANALYSIS_REQUEST,
    bootstrapServersProperty = "spring.kafka.bootstrap-servers"
)
class AnalysisEventConsumerTest {

    @Autowired
    private KafkaTemplate<
        String,
        EventEnvelope<AnalyzePullRequestEvent>
        > kafkaTemplate;

    @MockitoBean
    private AnalysisService analysisService;

    @Test
    void shouldConsumeAnalysisRequestFromKafka() {

        String correlationId =
            UUID.randomUUID().toString();

        AnalyzePullRequestEvent payload =
            new AnalyzePullRequestEvent(
                "StoryThreads",
                "releaseguard",
                1L
            );

        EventEnvelope<AnalyzePullRequestEvent> event =
            new EventEnvelope<>(
                UUID.randomUUID().toString(),
                "ANALYZE_PULL_REQUEST",
                Instant.now(),
                correlationId,
                payload
            );

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            event.getEventId(),
            event
        );

        verify(analysisService, timeout(10000))
            .analyzePullRequest(
                "StoryThreads",
                "releaseguard",
                1L
            );
    }
}
