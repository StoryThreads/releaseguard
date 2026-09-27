package com.releaseguard.kafka;

public final class KafkaTopics {

    public static final String ANALYSIS_REQUEST =
        "releaseguard.analysis.request";

    public static final String ANALYSIS_REQUEST_DLQ =
        "releaseguard.analysis.request.dlq";

    private KafkaTopics() {
    }
}
