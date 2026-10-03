package com.releaseguard.webhook;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class GitHubWebhookDto {

    private String action;
    private Long number;

    @JsonProperty("pull_request")
    private PullRequestDto pullRequest;

    private RepositoryDto repository;
    private UserDto sender;

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public Long getNumber() {
        return number;
    }

    public void setNumber(Long number) {
        this.number = number;
    }

    public PullRequestDto getPullRequest() {
        return pullRequest;
    }

    public void setPullRequest(PullRequestDto pullRequest) {
        this.pullRequest = pullRequest;
    }

    public RepositoryDto getRepository() {
        return repository;
    }

    public void setRepository(RepositoryDto repository) {
        this.repository = repository;
    }

    public UserDto getSender() {
        return sender;
    }

    public void setSender(UserDto sender) {
        this.sender = sender;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PullRequestDto {
        private Long number;
        private String title;
        private String state;
        private UserDto user;
        private BranchDto head;
        private BranchDto base;

        public Long getNumber() {
            return number;
        }

        public void setNumber(Long number) {
            this.number = number;
        }

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public String getState() {
            return state;
        }

        public void setState(String state) {
            this.state = state;
        }

        public UserDto getUser() {
            return user;
        }

        public void setUser(UserDto user) {
            this.user = user;
        }

        public BranchDto getHead() {
            return head;
        }

        public void setHead(BranchDto head) {
            this.head = head;
        }

        public BranchDto getBase() {
            return base;
        }

        public void setBase(BranchDto base) {
            this.base = base;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class RepositoryDto {
        private String name;

        @JsonProperty("full_name")
        private String fullName;

        private UserDto owner;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getFullName() {
            return fullName;
        }

        public void setFullName(String fullName) {
            this.fullName = fullName;
        }

        public UserDto getOwner() {
            return owner;
        }

        public void setOwner(UserDto owner) {
            this.owner = owner;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BranchDto {
        private String sha;
        private String ref;

        public String getSha() {
            return sha;
        }

        public void setSha(String sha) {
            this.sha = sha;
        }

        public String getRef() {
            return ref;
        }

        public void setRef(String ref) {
            this.ref = ref;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UserDto {
        private String login;

        public String getLogin() {
            return login;
        }

        public void setLogin(String login) {
            this.login = login;
        }
    }
}
