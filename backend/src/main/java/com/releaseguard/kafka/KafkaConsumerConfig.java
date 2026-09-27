package com.releaseguard.kafka;

import com.releaseguard.event.AnalyzePullRequestEvent;
import com.releaseguard.event.EventEnvelope;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

import java.util.HashMap;
import java.util.Map;

@Configuration
@EnableKafka
public class KafkaConsumerConfig {

    @Bean
    public ConsumerFactory<
        String,
        EventEnvelope<AnalyzePullRequestEvent>
        > analysisConsumerFactory(
        @Value("${spring.kafka.bootstrap-servers}")
        String bootstrapServers,
        @Value("${spring.kafka.consumer.group-id}")
        String groupId
    ) {

        Map<String, Object> properties =
            new HashMap<>();

        properties.put(
            ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG,
            bootstrapServers
        );

        properties.put(
            ConsumerConfig.GROUP_ID_CONFIG,
            groupId
        );

        properties.put(
            ConsumerConfig.AUTO_OFFSET_RESET_CONFIG,
            "earliest"
        );

        properties.put(
            ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG,
            false
        );

        properties.put(
            ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
            StringDeserializer.class
        );

        properties.put(
            ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
            KafkaEventDeserializer.class
        );

        return new DefaultKafkaConsumerFactory<>(
            properties
        );
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<
        String,
        EventEnvelope<AnalyzePullRequestEvent>
        > kafkaListenerContainerFactory(
        ConsumerFactory<
            String,
            EventEnvelope<AnalyzePullRequestEvent>
            > analysisConsumerFactory,
        DefaultErrorHandler kafkaErrorHandler
    ) {

        ConcurrentKafkaListenerContainerFactory<
            String,
            EventEnvelope<AnalyzePullRequestEvent>
            > factory =
            new ConcurrentKafkaListenerContainerFactory<>();

        factory.setConsumerFactory(
            analysisConsumerFactory
        );

        factory.setCommonErrorHandler(
            kafkaErrorHandler
        );

        return factory;
    }

    @Bean
    public DefaultErrorHandler kafkaErrorHandler(
        KafkaTemplate<
            String,
            EventEnvelope<AnalyzePullRequestEvent>
            > kafkaTemplate
    ) {

        DeadLetterPublishingRecoverer recoverer =
            new DeadLetterPublishingRecoverer(
                kafkaTemplate,
                (record, exception) ->
                    new TopicPartition(
                        KafkaTopics.ANALYSIS_REQUEST_DLQ,
                        record.partition()
                    )
            );

        FixedBackOff backOff =
            new FixedBackOff(
                1000L,
                2L
            );

        return new DefaultErrorHandler(
            recoverer,
            backOff
        );
    }
}
