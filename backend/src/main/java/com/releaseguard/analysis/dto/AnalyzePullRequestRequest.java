package com.releaseguard.analysis.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class AnalyzePullRequestRequest {

    @NotNull
    @Min(1)
    private Long projectId;

    @NotBlank
    private String owner;

    @NotBlank
    private String repository;

    @NotNull
    @Min(1)
    private Long pullRequestNumber;

    public Long getProjectId() {
        return projectId;
    }

    public void setProjectId(Long projectId) {
        this.projectId = projectId;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getRepository() {
        return repository;
    }

    public void setRepository(String repository) {
        this.repository = repository;
    }

    public Long getPullRequestNumber() {
        return pullRequestNumber;
    }

    public void setPullRequestNumber(Long pullRequestNumber) {
        this.pullRequestNumber = pullRequestNumber;
    }
}
