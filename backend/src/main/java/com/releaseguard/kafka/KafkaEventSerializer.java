package com.releaseguard.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.apache.kafka.common.serialization.Serializer;

public class KafkaEventSerializer<T> implements Serializer<T> {

    private final ObjectMapper objectMapper;

    public KafkaEventSerializer() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
    }

    @Override
    public byte[] serialize(String topic, T data) {

        if (data == null) {
            return null;
        }

        try {
            return objectMapper.writeValueAsBytes(data);
        } catch (Exception exception) {
            throw new IllegalStateException(
                "Failed to serialize Kafka event",
                exception
            );
        }
    }
}
