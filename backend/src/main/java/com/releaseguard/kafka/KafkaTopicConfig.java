package com.releaseguard.kafka;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaTopicConfig {

    @Bean
    public NewTopic analysisRequestTopic() {
        return TopicBuilder
            .name(KafkaTopics.ANALYSIS_REQUEST)
            .partitions(1)
            .replicas(1)
            .build();
    }

    @Bean
    public NewTopic analysisRequestDlqTopic() {
        return TopicBuilder
            .name(KafkaTopics.ANALYSIS_REQUEST_DLQ)
            .partitions(1)
            .replicas(1)
            .build();
    }
}
