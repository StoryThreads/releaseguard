package com.releaseguard.github;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GitHubPullRequestFilesTest {

    @Autowired
    private GitHubRestAdapter githubRestAdapter;

    @Test
    void shouldRetrievePullRequestFiles() {

        String owner = "StoryThreads";
        String repository = "releaseguard";
        long pullRequestNumber = 1;

        List<GitHubPullRequestFileResponse> files =
            githubRestAdapter.getPullRequestFiles(
                owner,
                repository,
                pullRequestNumber
            );

        assertNotNull(files);
        assertFalse(files.isEmpty());

        for (GitHubPullRequestFileResponse file : files) {

            assertNotNull(file.getFilename());
            assertNotNull(file.getStatus());

            assertTrue(file.getAdditions() >= 0);
            assertTrue(file.getDeletions() >= 0);
            assertTrue(file.getChanges() >= 0);
        }
    }
}
