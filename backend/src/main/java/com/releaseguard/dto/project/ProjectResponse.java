package com.releaseguard.dto.project;

import java.time.OffsetDateTime;

public class ProjectResponse {

    private Long id;
    private String name;
    private String description;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public ProjectResponse() {
    }

    public ProjectResponse(
        Long id,
        String name,
        String description,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
    ) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
