package com.releaseguard.kafka;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.test.EmbeddedKafkaBroker;
import org.springframework.kafka.test.context.EmbeddedKafka;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
@EmbeddedKafka(
    partitions = 1,
    topics = KafkaTopics.ANALYSIS_REQUEST,
    bootstrapServersProperty = "spring.kafka.bootstrap-servers"
)
class AnalysisEventProducerTest {

    @Autowired
    private AnalysisEventProducer producer;

    @Autowired
    private EmbeddedKafkaBroker embeddedKafka;

    @Test
    void shouldPublishAnalysisRequestEvent() throws Exception {

        String correlationId = "test-correlation-id";

        producer.publishAnalysisRequest(
            1L,
            "StoryThreads",
            "releaseguard",
            1L,
            correlationId
        );

        Map<String, Object> consumerProperties = new HashMap<>();

        consumerProperties.put(
            ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG,
            embeddedKafka.getBrokersAsString()
        );

        consumerProperties.put(
            ConsumerConfig.GROUP_ID_CONFIG,
            "releaseguard-producer-test"
        );

        consumerProperties.put(
            ConsumerConfig.AUTO_OFFSET_RESET_CONFIG,
            "earliest"
        );

        consumerProperties.put(
            ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
            StringDeserializer.class
        );

        consumerProperties.put(
            ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
            StringDeserializer.class
        );

        ConsumerFactory<String, String> consumerFactory =
            new DefaultKafkaConsumerFactory<>(
                consumerProperties
            );

        try (
            Consumer<String, String> consumer =
                consumerFactory.createConsumer()
        ) {

            consumer.subscribe(
                List.of(KafkaTopics.ANALYSIS_REQUEST)
            );

            ConsumerRecord<String, String> record = null;

            long deadline =
                System.currentTimeMillis() + 10_000;

            while (
                record == null
                    && System.currentTimeMillis() < deadline
            ) {

                var records =
                    consumer.poll(Duration.ofMillis(500));

                for (
                    ConsumerRecord<String, String> current : records
                ) {

                    if (
                        KafkaTopics.ANALYSIS_REQUEST.equals(
                            current.topic()
                        )
                    ) {

                        record = current;
                        break;
                    }
                }
            }

            assertNotNull(record);
            assertNotNull(record.value());

            ObjectMapper objectMapper =
                new ObjectMapper();

            JsonNode envelope =
                objectMapper.readTree(record.value());

            assertEquals(
                "ANALYZE_PULL_REQUEST",
                envelope
                    .get("eventType")
                    .asText()
            );

            assertEquals(
                correlationId,
                envelope
                    .get("correlationId")
                    .asText()
            );

            assertNotNull(
                envelope.get("eventId")
            );

            assertNotNull(
                envelope.get("occurredAt")
            );

            JsonNode payload =
                envelope.get("payload");

            assertNotNull(payload);

            assertEquals(
                "StoryThreads",
                payload
                    .get("owner")
                    .asText()
            );

            assertEquals(
                "releaseguard",
                payload
                    .get("repository")
                    .asText()
            );

            assertEquals(
                1L,
                payload
                    .get("pullRequestNumber")
                    .asLong()
            );
        }
    }
}
