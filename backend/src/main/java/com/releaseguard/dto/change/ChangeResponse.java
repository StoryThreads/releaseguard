package com.releaseguard.dto.change;

import java.time.OffsetDateTime;

public class ChangeResponse {

    private Long id;
    private Long sourceId;
    private String externalChangeId;
    private String title;
    private String author;
    private String baseRevision;
    private String headRevision;
    private String status;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public ChangeResponse() {
    }

    public ChangeResponse(
        Long id,
        Long sourceId,
        String externalChangeId,
        String title,
        String author,
        String baseRevision,
        String headRevision,
        String status,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
    ) {
        this.id = id;
        this.sourceId = sourceId;
        this.externalChangeId = externalChangeId;
        this.title = title;
        this.author = author;
        this.baseRevision = baseRevision;
        this.headRevision = headRevision;
        this.status = status;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public Long getSourceId() {
        return sourceId;
    }

    public String getExternalChangeId() {
        return externalChangeId;
    }

    public String getTitle() {
        return title;
    }

    public String getAuthor() {
        return author;
    }

    public String getBaseRevision() {
        return baseRevision;
    }

    public String getHeadRevision() {
        return headRevision;
    }

    public String getStatus() {
        return status;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
