-- ============================================================
-- ReleaseGuard V3
-- Kafka processed event tracking / idempotency
-- ============================================================

CREATE TABLE processed_events (
                                  event_id VARCHAR(100) PRIMARY KEY,

                                  event_type VARCHAR(100) NOT NULL,

                                  correlation_id VARCHAR(100) NOT NULL,

                                  status VARCHAR(30) NOT NULL,

                                  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                                  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_processed_events_status
    ON processed_events(status);

CREATE INDEX idx_processed_events_correlation_id
    ON processed_events(correlation_id);
