package com.releaseguard.event;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertEquals;

class EventEnvelopeTest {

    @Test
    void shouldCreateAnalyzePullRequestEventEnvelope() {

        Instant occurredAt =
            Instant.parse("2026-09-27T10:00:00Z");

        Long projectId = 292L;

        AnalyzePullRequestEvent payload =
            new AnalyzePullRequestEvent(
                projectId,
                "StoryThreads",
                "releaseguard",
                1L
            );

        EventEnvelope<AnalyzePullRequestEvent> envelope =
            new EventEnvelope<>(
                "event-123",
                EventType.ANALYZE_PULL_REQUEST.name(),
                occurredAt,
                "correlation-123",
                payload
            );

        assertEquals(
            "event-123",
            envelope.getEventId()
        );

        assertEquals(
            "ANALYZE_PULL_REQUEST",
            envelope.getEventType()
        );

        assertEquals(
            occurredAt,
            envelope.getOccurredAt()
        );

        assertEquals(
            "correlation-123",
            envelope.getCorrelationId()
        );

        assertEquals(
            projectId,
            envelope.getPayload().getProjectId()
        );

        assertEquals(
            "StoryThreads",
            envelope.getPayload().getOwner()
        );

        assertEquals(
            "releaseguard",
            envelope.getPayload().getRepository()
        );

        assertEquals(
            1L,
            envelope.getPayload().getPullRequestNumber()
        );
    }
}
