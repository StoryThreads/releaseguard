package com.releaseguard.dto.source;

import java.time.OffsetDateTime;

public class SourceResponse {

    private Long id;
    private Long projectId;
    private String provider;
    private String repositoryOwner;
    private String repositoryName;
    private String defaultBranch;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public SourceResponse() {
    }

    public SourceResponse(
        Long id,
        Long projectId,
        String provider,
        String repositoryOwner,
        String repositoryName,
        String defaultBranch,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
    ) {
        this.id = id;
        this.projectId = projectId;
        this.provider = provider;
        this.repositoryOwner = repositoryOwner;
        this.repositoryName = repositoryName;
        this.defaultBranch = defaultBranch;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public Long getProjectId() {
        return projectId;
    }

    public String getProvider() {
        return provider;
    }

    public String getRepositoryOwner() {
        return repositoryOwner;
    }

    public String getRepositoryName() {
        return repositoryName;
    }

    public String getDefaultBranch() {
        return defaultBranch;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
