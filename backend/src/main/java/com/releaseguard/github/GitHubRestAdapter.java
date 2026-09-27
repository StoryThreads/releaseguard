package com.releaseguard.github;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import java.util.List;

import org.springframework.core.ParameterizedTypeReference;

@Component
public class GitHubRestAdapter {

    private final RestClient restClient;

    public GitHubRestAdapter(
            RestClient.Builder restClientBuilder,
            GitHubProperties githubProperties) {
        this.restClient = restClientBuilder
                .baseUrl(githubProperties.getApiUrl())
                .defaultHeader(
                        "Authorization",
                        "Bearer " + githubProperties.getToken())
                .defaultHeader(
                        "Accept",
                        "application/vnd.github+json")
                .defaultHeader(
                        "X-GitHub-Api-Version",
                        "2022-11-28")
                .build();
    }

    public String getAuthenticatedUser() {

        return restClient
                .get()
                .uri("/user")
                .retrieve()
                .body(String.class);
    }

    public GitHubPullRequestResponse getPullRequest(
        String owner,
        String repository,
        long pullRequestNumber
    ) {
        return restClient
            .get()
            .uri("/repos/{owner}/{repository}/pulls/{pullRequestNumber}",
                owner,
                repository,
                pullRequestNumber)
            .retrieve()
            .body(GitHubPullRequestResponse.class);
    }

    public List<GitHubPullRequestFileResponse> getPullRequestFiles(
        String owner,
        String repository,
        long pullRequestNumber
    ) {
        return restClient
            .get()
            .uri("/repos/{owner}/{repository}/pulls/{pullRequestNumber}/files",
                owner,
                repository,
                pullRequestNumber)
            .retrieve()
            .body(new ParameterizedTypeReference<>() {});
    }
}
