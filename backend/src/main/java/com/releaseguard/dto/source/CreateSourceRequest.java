package com.releaseguard.dto.source;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public class CreateSourceRequest {

    @NotNull(message = "Project ID is required")
    private Long projectId;

    @NotBlank(message = "Provider is required")
    @Size(max = 30, message = "Provider must not exceed 30 characters")
    private String provider;

    @NotBlank(message = "Repository owner is required")
    @Size(max = 100, message = "Repository owner must not exceed 100 characters")
    private String repositoryOwner;

    @NotBlank(message = "Repository name is required")
    @Size(max = 200, message = "Repository name must not exceed 200 characters")
    private String repositoryName;

    @NotBlank(message = "Default branch is required")
    @Size(max = 100, message = "Default branch must not exceed 100 characters")
    private String defaultBranch;

    public CreateSourceRequest() {
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

    public void setProjectId(Long projectId) {
        this.projectId = projectId;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public void setRepositoryOwner(String repositoryOwner) {
        this.repositoryOwner = repositoryOwner;
    }

    public void setRepositoryName(String repositoryName) {
        this.repositoryName = repositoryName;
    }

    public void setDefaultBranch(String defaultBranch) {
        this.defaultBranch = defaultBranch;
    }
}
