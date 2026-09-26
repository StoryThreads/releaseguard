-- ============================================================
-- ReleaseGuard V1
-- Initial database schema
-- ============================================================

-- ============================================================
-- 1. PROJECTS
-- ============================================================

CREATE TABLE projects (
                          id BIGSERIAL PRIMARY KEY,

                          name VARCHAR(100) NOT NULL,
                          description VARCHAR(500),

                          created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                          CONSTRAINT uk_projects_name UNIQUE (name)
);


-- ============================================================
-- 2. SOURCES
-- ============================================================

CREATE TABLE sources (
                         id BIGSERIAL PRIMARY KEY,

                         project_id BIGINT NOT NULL,

                         provider VARCHAR(30) NOT NULL,
                         repository_owner VARCHAR(100) NOT NULL,
                         repository_name VARCHAR(200) NOT NULL,
                         default_branch VARCHAR(100) NOT NULL DEFAULT 'main',

                         created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                         updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                         CONSTRAINT fk_sources_project
                             FOREIGN KEY (project_id)
                                 REFERENCES projects(id)
                                 ON DELETE RESTRICT,

                         CONSTRAINT uk_sources_repository
                             UNIQUE (
                                     project_id,
                                     provider,
                                     repository_owner,
                                     repository_name
                                 )
);


-- ============================================================
-- 3. CHANGES
-- ============================================================

CREATE TABLE changes (
                         id BIGSERIAL PRIMARY KEY,

                         source_id BIGINT NOT NULL,

                         external_change_id VARCHAR(100) NOT NULL,
                         title VARCHAR(500) NOT NULL,
                         author VARCHAR(200) NOT NULL,

                         base_revision VARCHAR(100) NOT NULL,
                         head_revision VARCHAR(100) NOT NULL,

                         status VARCHAR(30) NOT NULL,

                         created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                         updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                         CONSTRAINT fk_changes_source
                             FOREIGN KEY (source_id)
                                 REFERENCES sources(id)
                                 ON DELETE RESTRICT,

                         CONSTRAINT uk_changes_external_id
                             UNIQUE (
                                     source_id,
                                     external_change_id
                                 )
);


-- ============================================================
-- 4. ANALYSIS JOBS
-- ============================================================

CREATE TABLE analysis_jobs (
                               id BIGSERIAL PRIMARY KEY,

                               change_id BIGINT NOT NULL,

                               status VARCHAR(30) NOT NULL,
                               correlation_id UUID NOT NULL,

                               started_at TIMESTAMPTZ,
                               completed_at TIMESTAMPTZ,

                               error_code VARCHAR(100),
                               error_message VARCHAR(1000),

                               created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                               CONSTRAINT fk_analysis_jobs_change
                                   FOREIGN KEY (change_id)
                                       REFERENCES changes(id)
                                       ON DELETE RESTRICT,

                               CONSTRAINT uk_analysis_jobs_correlation
                                   UNIQUE (correlation_id)
);


-- ============================================================
-- 5. INDEXES
-- ============================================================

CREATE INDEX idx_sources_project_id
    ON sources(project_id);

CREATE INDEX idx_changes_source_id
    ON changes(source_id);

CREATE INDEX idx_changes_status
    ON changes(status);

CREATE INDEX idx_analysis_jobs_change_id
    ON analysis_jobs(change_id);

CREATE INDEX idx_analysis_jobs_status
    ON analysis_jobs(status);

CREATE INDEX idx_analysis_jobs_created_at
    ON analysis_jobs(created_at);
