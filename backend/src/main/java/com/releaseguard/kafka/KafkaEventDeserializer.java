package com.releaseguard.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import org.apache.kafka.common.serialization.Deserializer;

public class KafkaEventDeserializer
    implements Deserializer<EventEnvelope<AnalyzePullRequestEvent>> {

    private final ObjectMapper objectMapper;

    public KafkaEventDeserializer() {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
    }

    @Override
    public EventEnvelope<AnalyzePullRequestEvent> deserialize(
        String topic,
        byte[] data
    ) {

        if (data == null) {
            return null;
        }

        try {
            return objectMapper.readValue(
                data,
                objectMapper.getTypeFactory().constructParametricType(
                    EventEnvelope.class,
                    AnalyzePullRequestEvent.class
                )
            );
        } catch (Exception exception) {
            throw new IllegalStateException(
                "Failed to deserialize Kafka event",
                exception
            );
        }
    }
}
