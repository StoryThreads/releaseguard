package com.releaseguard.github;

import com.fasterxml.jackson.core.type.TypeReference;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import java.util.List;

public final class GitHubTypeReferences {
    public static final TypeReference<List<GitHubPullRequestFileResponse>> PULL_REQUEST_FILES =
        new TypeReference<>() {};

    private GitHubTypeReferences() {}
}
