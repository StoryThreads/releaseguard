package com.releaseguard.analysis;

import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.analyzer.AnalyzerContext;
import com.releaseguard.analyzer.AnalyzerEngine;
import com.releaseguard.analyzer.AnalyzerType;
import com.releaseguard.analyzer.Finding;
import com.releaseguard.analyzer.FindingSeverity;
import com.releaseguard.analyzer.FindingType;
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
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AnalysisServiceTest {

    @Mock
    private GitHubRestAdapter githubRestAdapter;

    @Mock
    private GitHubChangeSnapshotMapper snapshotMapper;

    @Mock
    private SourceService sourceService;

    @Mock
    private ChangeService changeService;

    @Mock
    private AnalyzerEngine analyzerEngine;

    @Mock
    private FindingPersistenceService findingPersistenceService;

    @InjectMocks
    private AnalysisService analysisService;

    @Test
    void shouldRunAnalyzersAndPersistFindings() {

        GitHubPullRequestResponse pullRequest = new GitHubPullRequestResponse();
        pullRequest.setNumber(1L);
        pullRequest.setTitle("Test PR");
        pullRequest.setState("open");

        GitHubPullRequestResponse.User user =
            new GitHubPullRequestResponse.User();
        user.setLogin("test-user");
        pullRequest.setUser(user);

        GitHubPullRequestResponse.Branch base =
            new GitHubPullRequestResponse.Branch();
        base.setSha("base-sha");
        base.setRef("main");
        pullRequest.setBase(base);

        GitHubPullRequestResponse.Branch head =
            new GitHubPullRequestResponse.Branch();
        head.setSha("head-sha");
        head.setRef("feature/test");
        pullRequest.setHead(head);

        ChangeSnapshot snapshot = new ChangeSnapshot();
        snapshot.setPullRequestNumber(1L);
        snapshot.setOwner("owner");
        snapshot.setRepository("repo");
        snapshot.setTitle("Test PR");

        Source source = new Source();

        Change change = new Change();
        change.setExternalChangeId("1");

        Finding finding = new Finding(
            AnalyzerType.CODE,
            FindingType.CODE_ISSUE,
            FindingSeverity.MEDIUM,
            "CODE-001",
            "Test finding",
            "Test message",
            "Test.java",
            10
        );

        when(githubRestAdapter.getPullRequest("owner", "repo", 1L))
            .thenReturn(pullRequest);
        when(githubRestAdapter.getPullRequestFiles("owner", "repo", 1L))
            .thenReturn(List.<GitHubPullRequestFileResponse>of());
        when(snapshotMapper.map(
            eq("owner"), eq("repo"), eq(pullRequest), any()
        )).thenReturn(snapshot);
        when(sourceService.getGitHubSource("owner", "repo"))
            .thenReturn(source);
        when(changeService.getOrCreateChange(
            any(), any(), any(), any(), any(), any(), any()
        )).thenReturn(change);
        when(analyzerEngine.analyze(any(AnalyzerContext.class)))
            .thenReturn(List.of(finding));

        AnalyzePullRequestResponse response =
            analysisService.analyzePullRequest("owner", "repo", 1L);

        assertSame(snapshot, response.getSnapshot());
        assertSame(change.getId(), response.getChangeId());
        assertEquals(List.of(finding), response.getFindings());

        ArgumentCaptor<AnalyzerContext> contextCaptor =
            ArgumentCaptor.forClass(AnalyzerContext.class);

        verify(analyzerEngine).analyze(contextCaptor.capture());
        assertSame(snapshot, contextCaptor.getValue().changeSnapshot());

        verify(findingPersistenceService)
            .replaceFindings(change, List.of(finding));
    }
}
