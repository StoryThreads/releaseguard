CREATE TABLE findings (
                          id BIGSERIAL PRIMARY KEY,

                          change_id BIGINT NOT NULL,

                          analyzer_type VARCHAR(50) NOT NULL,
                          finding_type VARCHAR(50) NOT NULL,
                          severity VARCHAR(30) NOT NULL,

                          rule_id VARCHAR(100) NOT NULL,

                          title VARCHAR(500) NOT NULL,
                          message VARCHAR(2000) NOT NULL,

                          file_path VARCHAR(1000),
                          line_number INTEGER,

                          created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                          CONSTRAINT fk_findings_change
                              FOREIGN KEY (change_id)
                                  REFERENCES changes(id)
                                  ON DELETE RESTRICT
);

CREATE INDEX idx_findings_change_id
    ON findings(change_id);

CREATE INDEX idx_findings_severity
    ON findings(severity);

CREATE INDEX idx_findings_rule_id
    ON findings(rule_id);
