package com.releaseguard.kafka;

/**
 * Thrown when an incoming Kafka event encounters an active distributed lease held by another worker.
 * Throwing this exception ensures that the Kafka consumer does NOT silently acknowledge/commit
 * the record, allowing Kafka's DefaultErrorHandler to execute retry policies or route to DLQ
 * if the in-progress lease was abandoned by a crashed worker.
 */
public class EventProcessingInProgressException extends IllegalStateException {

    public EventProcessingInProgressException(String message) {
        super(message);
    }
}
