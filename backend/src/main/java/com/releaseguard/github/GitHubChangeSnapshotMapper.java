package com.releaseguard.github;

import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class GitHubChangeSnapshotMapper {

    public ChangeSnapshot map(
        String owner,
        String repository,
        GitHubPullRequestResponse pullRequest,
        List<GitHubPullRequestFileResponse> files
    ) {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        snapshot.setPullRequestNumber(pullRequest.getNumber());
        snapshot.setOwner(owner);
        snapshot.setRepository(repository);
        snapshot.setTitle(pullRequest.getTitle());

        if (pullRequest.getHead() != null) {
            snapshot.setSourceBranch(
                pullRequest.getHead().getRef()
            );

            snapshot.setHeadSha(
                pullRequest.getHead().getSha()
            );
        }

        if (pullRequest.getBase() != null) {
            snapshot.setTargetBranch(
                pullRequest.getBase().getRef()
            );
        }

        List<ChangeSnapshot.ChangedFile> changedFiles =
            files.stream()
                .map(this::mapFile)
                .toList();

        snapshot.setChangedFiles(changedFiles);

        snapshot.setTotalAdditions(
            files.stream()
                .mapToInt(f -> f != null ? f.getAdditions() : 0)
                .sum()
        );

        snapshot.setTotalDeletions(
            files.stream()
                .mapToInt(f -> f != null ? f.getDeletions() : 0)
                .sum()
        );

        snapshot.setTotalChanges(
            files.stream()
                .mapToInt(f -> f != null ? f.getChanges() : 0)
                .sum()
        );

        return snapshot;
    }

    private ChangeSnapshot.ChangedFile mapFile(
        GitHubPullRequestFileResponse file
    ) {

        ChangeSnapshot.ChangedFile changedFile =
            new ChangeSnapshot.ChangedFile();

        changedFile.setFilename(file.getFilename());
        changedFile.setStatus(file.getStatus());
        changedFile.setAdditions(file.getAdditions());
        changedFile.setDeletions(file.getDeletions());
        changedFile.setChanges(file.getChanges());
        changedFile.setPatch(file.getPatch());

        return changedFile;
    }
}
