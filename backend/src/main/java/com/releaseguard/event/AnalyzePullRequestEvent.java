package com.releaseguard.event;

public class AnalyzePullRequestEvent {

    private Long projectId;

    private String owner;

    private String repository;

    private Long pullRequestNumber;

    public AnalyzePullRequestEvent() {
    }

    public AnalyzePullRequestEvent(
        Long projectId,
        String owner,
        String repository,
        Long pullRequestNumber
    ) {
        this.projectId = projectId;
        this.owner = owner;
        this.repository = repository;
        this.pullRequestNumber = pullRequestNumber;
    }

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
