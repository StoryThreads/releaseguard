package com.releaseguard.dto.change;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public class CreateChangeRequest {

    @NotNull(message = "Source ID is required")
    private Long sourceId;

    @NotBlank(message = "External change ID is required")
    @Size(max = 100, message = "External change ID must not exceed 100 characters")
    private String externalChangeId;

    @NotBlank(message = "Title is required")
    @Size(max = 500, message = "Title must not exceed 500 characters")
    private String title;

    @NotBlank(message = "Author is required")
    @Size(max = 200, message = "Author must not exceed 200 characters")
    private String author;

    @NotBlank(message = "Base revision is required")
    @Size(max = 100, message = "Base revision must not exceed 100 characters")
    private String baseRevision;

    @NotBlank(message = "Head revision is required")
    @Size(max = 100, message = "Head revision must not exceed 100 characters")
    private String headRevision;

    @NotBlank(message = "Status is required")
    @Size(max = 30, message = "Status must not exceed 30 characters")
    private String status;

    public CreateChangeRequest() {
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

    public void setSourceId(Long sourceId) {
        this.sourceId = sourceId;
    }

    public void setExternalChangeId(String externalChangeId) {
        this.externalChangeId = externalChangeId;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public void setBaseRevision(String baseRevision) {
        this.baseRevision = baseRevision;
    }

    public void setHeadRevision(String headRevision) {
        this.headRevision = headRevision;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
