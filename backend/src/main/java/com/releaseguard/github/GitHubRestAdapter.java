package com.releaseguard.github;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import java.util.List;

@Component
public class GitHubRestAdapter {

    private final RestClient restClient;

    public GitHubRestAdapter(
            RestClient.Builder restClientBuilder,
            GitHubProperties githubProperties) {
        RestClient.Builder builder = restClientBuilder
                .baseUrl(githubProperties.getApiUrl())
                .defaultHeader(
                        "Accept",
                        "application/vnd.github+json")
                .defaultHeader(
                        "X-GitHub-Api-Version",
                        "2022-11-28")
                .defaultHeader(
                        "User-Agent",
                        "ReleaseGuard-App/1.0");

        String token = githubProperties.getToken();
        if (token != null && !token.isBlank() && !"null".equalsIgnoreCase(token.trim())) {
            builder.defaultHeader("Authorization", "Bearer " + token.trim());
        }

        this.restClient = builder.build();
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

    private static final com.fasterxml.jackson.databind.ObjectMapper JSON_MAPPER =
        new com.fasterxml.jackson.databind.ObjectMapper()
            .configure(com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    public List<GitHubPullRequestFileResponse> getPullRequestFiles(
        String owner,
        String repository,
        long pullRequestNumber
    ) {
        try {
            String rawJson = restClient
                .get()
                .uri("/repos/{owner}/{repository}/pulls/{pullRequestNumber}/files",
                    owner,
                    repository,
                    pullRequestNumber)
                .retrieve()
                .body(String.class);

            if (rawJson == null || rawJson.isBlank() || !rawJson.trim().startsWith("[")) {
                return List.of();
            }
            return JSON_MAPPER.readValue(rawJson, GitHubTypeReferences.PULL_REQUEST_FILES);
        } catch (Exception e) {
            return List.of();
        }
    }

    public List<GitHubPullRequestResponse> getRecentPullRequests(
        String owner,
        String repository,
        String state,
        int perPage
    ) {
        String prState = (state != null && !state.isBlank()) ? state : "all";
        int limit = perPage > 0 ? perPage : 15;
        try {
            String rawJson = restClient
                .get()
                .uri("/repos/{owner}/{repository}/pulls?state={state}&per_page={perPage}&sort=updated&direction=desc",
                    owner,
                    repository,
                    prState,
                    limit)
                .retrieve()
                .body(String.class);

            if (rawJson == null || rawJson.isBlank() || !rawJson.trim().startsWith("[")) {
                System.err.println("GitHub unexpected response for " + owner + "/" + repository + ": " + rawJson);
                return List.of();
            }

            return JSON_MAPPER.readValue(
                rawJson,
                JSON_MAPPER.getTypeFactory().constructCollectionType(List.class, GitHubPullRequestResponse.class)
            );
        } catch (Exception e) {
            System.err.println("Failed to fetch recent PRs for " + owner + "/" + repository + ": " + e.getMessage());
            return List.of();
        }
    }
}
