package com.releaseguard.analysis;

import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.github.GitHubChangeSnapshotMapper;
import com.releaseguard.github.GitHubRestAdapter;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AnalysisService {

    private final GitHubRestAdapter githubRestAdapter;
    private final GitHubChangeSnapshotMapper snapshotMapper;

    public AnalysisService(
        GitHubRestAdapter githubRestAdapter,
        GitHubChangeSnapshotMapper snapshotMapper
    ) {
        this.githubRestAdapter = githubRestAdapter;
        this.snapshotMapper = snapshotMapper;
    }

    public AnalyzePullRequestResponse analyzePullRequest(
        String owner,
        String repository,
        long pullRequestNumber
    ) {

        GitHubPullRequestResponse pullRequest =
            githubRestAdapter.getPullRequest(
                owner,
                repository,
                pullRequestNumber
            );

        List<GitHubPullRequestFileResponse> files =
            githubRestAdapter.getPullRequestFiles(
                owner,
                repository,
                pullRequestNumber
            );

        ChangeSnapshot snapshot =
            snapshotMapper.map(
                owner,
                repository,
                pullRequest,
                files
            );

        return new AnalyzePullRequestResponse(snapshot);
    }
}
