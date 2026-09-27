package com.releaseguard.github;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import java.util.List;
import org.junit.jupiter.api.Test;

class GitHubChangeSnapshotMapperTest {

    private final GitHubChangeSnapshotMapper mapper =
        new GitHubChangeSnapshotMapper();

    @Test
    void shouldMapGitHubPullRequestToChangeSnapshot() {

        GitHubPullRequestResponse pullRequest =
            new GitHubPullRequestResponse();

        pullRequest.setNumber(7L);
        pullRequest.setTitle("Test PR");

        GitHubPullRequestResponse.Branch head =
            new GitHubPullRequestResponse.Branch();

        head.setRef("feature/test");
        head.setSha("abc123");

        pullRequest.setHead(head);

        GitHubPullRequestResponse.Branch base =
            new GitHubPullRequestResponse.Branch();

        base.setRef("main");

        pullRequest.setBase(base);

        GitHubPullRequestFileResponse file =
            new GitHubPullRequestFileResponse();

        file.setFilename("README.md");
        file.setStatus("modified");
        file.setAdditions(5);
        file.setDeletions(2);
        file.setChanges(7);
        file.setPatch("@@ test patch");

        ChangeSnapshot snapshot =
            mapper.map(
                "test-owner",
                "releaseguard",
                pullRequest,
                List.of(file)
            );

        assertNotNull(snapshot);

        assertEquals(7L, snapshot.getPullRequestNumber());
        assertEquals("test-owner", snapshot.getOwner());
        assertEquals("releaseguard", snapshot.getRepository());

        assertEquals("Test PR", snapshot.getTitle());

        assertEquals(
            "feature/test",
            snapshot.getSourceBranch()
        );

        assertEquals(
            "main",
            snapshot.getTargetBranch()
        );

        assertEquals(
            "abc123",
            snapshot.getHeadSha()
        );

        assertEquals(1, snapshot.getChangedFiles().size());

        assertEquals(
            "README.md",
            snapshot.getChangedFiles()
                .getFirst()
                .getFilename()
        );

        assertEquals(5, snapshot.getTotalAdditions());
        assertEquals(2, snapshot.getTotalDeletions());
        assertEquals(7, snapshot.getTotalChanges());
    }
}
