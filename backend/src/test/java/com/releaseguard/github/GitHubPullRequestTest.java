package com.releaseguard.github;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.releaseguard.github.dto.GitHubPullRequestResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GitHubPullRequestTest {

    @Autowired
    private GitHubRestAdapter githubRestAdapter;

    @Test
    void shouldRetrievePullRequestMetadata() {

        String owner = "StoryThreads";
        String repository = "releaseguard";
        long pullRequestNumber = 1;

        GitHubPullRequestResponse pullRequest =
            githubRestAdapter.getPullRequest(
                owner,
                repository,
                pullRequestNumber
            );

        assertNotNull(pullRequest);
        assertNotNull(pullRequest.getNumber());
        assertNotNull(pullRequest.getTitle());
        assertNotNull(pullRequest.getState());

        assertTrue(
            pullRequest.getNumber() == pullRequestNumber
        );
    }
}
