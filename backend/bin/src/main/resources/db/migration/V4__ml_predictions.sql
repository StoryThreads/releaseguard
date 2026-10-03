-- ============================================================
-- ReleaseGuard V4
-- ML prediction persistence
-- ============================================================

CREATE TABLE ml_predictions (
    id BIGSERIAL PRIMARY KEY,

    change_id BIGINT NOT NULL,

    risk_level VARCHAR(20) NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,

    class_probabilities JSONB NOT NULL,
    feature_vector JSONB NOT NULL,

    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(30) NOT NULL,
    feature_version VARCHAR(30) NOT NULL,
    dataset_version VARCHAR(30) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ml_predictions_change
        FOREIGN KEY (change_id)
        REFERENCES changes(id)
        ON DELETE RESTRICT,

    CONSTRAINT uk_ml_predictions_change
        UNIQUE (change_id)
);

CREATE INDEX idx_ml_predictions_change_id
    ON ml_predictions(change_id);

CREATE INDEX idx_ml_predictions_model
    ON ml_predictions(model_name, model_version);
