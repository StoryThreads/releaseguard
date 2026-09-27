package com.releaseguard.analysis;

import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.analyzer.AnalyzerContext;
import com.releaseguard.analyzer.AnalyzerEngine;
import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.entity.Change;
import com.releaseguard.entity.Source;
import com.releaseguard.github.GitHubChangeSnapshotMapper;
import com.releaseguard.github.GitHubRestAdapter;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import com.releaseguard.service.ChangeService;
import com.releaseguard.service.FindingPersistenceService;
import com.releaseguard.service.SourceService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AnalysisService {

    private final GitHubRestAdapter githubRestAdapter;
    private final GitHubChangeSnapshotMapper snapshotMapper;
    private final SourceService sourceService;
    private final ChangeService changeService;
    private final AnalyzerEngine analyzerEngine;
    private final FindingPersistenceService findingPersistenceService;

    public AnalysisService(
        GitHubRestAdapter githubRestAdapter,
        GitHubChangeSnapshotMapper snapshotMapper,
        SourceService sourceService,
        ChangeService changeService,
        AnalyzerEngine analyzerEngine,
        FindingPersistenceService findingPersistenceService
    ) {
        this.githubRestAdapter = githubRestAdapter;
        this.snapshotMapper = snapshotMapper;
        this.sourceService = sourceService;
        this.changeService = changeService;
        this.analyzerEngine = analyzerEngine;
        this.findingPersistenceService = findingPersistenceService;
    }

    @Transactional
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

        Source source =
            sourceService.getGitHubSource(owner, repository);

        String author = pullRequest.getUser() != null
            ? pullRequest.getUser().getLogin()
            : "unknown";

        String baseRevision = pullRequest.getBase() != null
            ? pullRequest.getBase().getSha()
            : "unknown";

        String headRevision = pullRequest.getHead() != null
            ? pullRequest.getHead().getSha()
            : "unknown";

        String status = pullRequest.getState() != null
            ? pullRequest.getState()
            : "unknown";

        Change change = changeService.getOrCreateChange(
            source.getId(),
            String.valueOf(pullRequestNumber),
            snapshot.getTitle(),
            author,
            baseRevision,
            headRevision,
            status
        );

        AnalyzerContext context =
            new AnalyzerContext(snapshot);

        List<Finding> findings =
            analyzerEngine.analyze(context);

        findingPersistenceService.replaceFindings(
            change,
            findings
        );

        return new AnalyzePullRequestResponse(
            snapshot,
            change.getId(),
            findings
        );
    }
}
