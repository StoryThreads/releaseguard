package com.releaseguard.kafka;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.entity.ProcessedEvent;
import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import com.releaseguard.repository.ProcessedEventRepository;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.context.EmbeddedKafka;
import org.springframework.kafka.test.EmbeddedKafkaBroker;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.kafka.test.utils.KafkaTestUtils;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.timeout;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.when;

@SpringBootTest
@EmbeddedKafka(
    partitions = 1,
    topics = {
        KafkaTopics.ANALYSIS_REQUEST,
        KafkaTopics.ANALYSIS_REQUEST_DLQ
    },
    bootstrapServersProperty = "spring.kafka.bootstrap-servers"
)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class KafkaReliabilityTest {

    private static final Long PROJECT_ID = 292L;

    @Autowired
    private KafkaTemplate<
        String,
        EventEnvelope<AnalyzePullRequestEvent>
        > kafkaTemplate;

    @Autowired
    private EmbeddedKafkaBroker embeddedKafka;

    @Autowired
    private ProcessedEventRepository processedEventRepository;

    @MockitoBean
    private AnalysisService analysisService;

    @Test
    void shouldRetryFailedAnalysisAndEventuallySucceed()
        throws InterruptedException {

        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        when(
            analysisService.analyzePullRequest(
                PROJECT_ID,
                "StoryThreads",
                "releaseguard",
                1L
            )
        )
            .thenThrow(new IllegalStateException("temporary failure"))
            .thenReturn(null);

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            eventId,
            event
        );

        verify(
            analysisService,
            timeout(10000).times(2)
        ).analyzePullRequest(
            PROJECT_ID,
            "StoryThreads",
            "releaseguard",
            1L
        );

        waitUntilEventCompleted(eventId);

        ProcessedEvent processedEvent =
            processedEventRepository.findById(eventId).orElseThrow();

        assertEquals("COMPLETED", processedEvent.getStatus());
    }

    @Test
    void shouldSendFailedEventToDlq() {

        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        doThrow(new IllegalStateException("simulated analysis failure"))
            .when(analysisService)
            .analyzePullRequest(
                PROJECT_ID,
                "StoryThreads",
                "releaseguard",
                1L
            );

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            eventId,
            event
        );

        verify(
            analysisService,
            timeout(10000).times(3)
        ).analyzePullRequest(
            PROJECT_ID,
            "StoryThreads",
            "releaseguard",
            1L
        );

        Map<String, Object> properties =
            createConsumerProperties("releaseguard-dlq-test");

        try (
            Consumer<String, String> consumer =
                new DefaultKafkaConsumerFactory<String, String>(
                    properties
                ).createConsumer()
        ) {
            embeddedKafka.consumeFromAnEmbeddedTopic(
                consumer,
                KafkaTopics.ANALYSIS_REQUEST_DLQ
            );

            ConsumerRecord<String, String> record =
                KafkaTestUtils.getSingleRecord(
                    consumer,
                    KafkaTopics.ANALYSIS_REQUEST_DLQ,
                    Duration.ofSeconds(10)
                );

            assertNotNull(record);
        }
    }

    @Test
    void shouldProcessSameEventOnlyOnce()
        throws InterruptedException {

        String eventId = UUID.randomUUID().toString();
        EventEnvelope<AnalyzePullRequestEvent> event = createEvent(eventId);

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            eventId,
            event
        );

        verify(
            analysisService,
            timeout(10000).times(1)
        ).analyzePullRequest(
            PROJECT_ID,
            "StoryThreads",
            "releaseguard",
            1L
        );

        waitUntilEventCompleted(eventId);

        kafkaTemplate.send(
            KafkaTopics.ANALYSIS_REQUEST,
            eventId,
            event
        );

        Thread.sleep(2000);

        verify(
            analysisService,
            times(1)
        ).analyzePullRequest(
            PROJECT_ID,
            "StoryThreads",
            "releaseguard",
            1L
        );

        ProcessedEvent processedEvent =
            processedEventRepository.findById(eventId).orElseThrow();

        assertEquals("COMPLETED", processedEvent.getStatus());
    }

    private void waitUntilEventCompleted(String eventId)
        throws InterruptedException {

        long timeoutMillis = System.currentTimeMillis() + 10000;

        while (System.currentTimeMillis() < timeoutMillis) {
            ProcessedEvent event =
                processedEventRepository.findById(eventId).orElse(null);

            if (
                event != null
                    && "COMPLETED".equals(event.getStatus())
            ) {
                return;
            }

            Thread.sleep(100);
        }

        throw new AssertionError(
            "Event was not marked COMPLETED within timeout: " + eventId
        );
    }

    private Map<String, Object> createConsumerProperties(String groupId) {

        Map<String, Object> properties = new HashMap<>();

        properties.put(
            ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG,
            embeddedKafka.getBrokersAsString()
        );
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        properties.put(
            ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
            StringDeserializer.class
        );
        properties.put(
            ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
            StringDeserializer.class
        );

        return properties;
    }

    private EventEnvelope<AnalyzePullRequestEvent> createEvent(String eventId) {

        return new EventEnvelope<>(
            eventId,
            "ANALYZE_PULL_REQUEST",
            Instant.now(),
            UUID.randomUUID().toString(),
            new AnalyzePullRequestEvent(
                PROJECT_ID,
                "StoryThreads",
                "releaseguard",
                1L
            )
        );
    }
}
