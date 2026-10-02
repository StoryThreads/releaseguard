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
import com.releaseguard.ml.MlPredictionClient;
import com.releaseguard.ml.dto.MlPredictionResponse;
import com.releaseguard.service.ChangeService;
import com.releaseguard.service.FindingPersistenceService;
import com.releaseguard.service.MlPredictionPersistenceService;
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

    @Mock
    private MlPredictionClient mlPredictionClient;

    @Mock
    private MlPredictionPersistenceService mlPredictionPersistenceService;

    @InjectMocks
    private AnalysisService analysisService;

    @Test
    void shouldRunAnalyzersAndPersistFindings() {

        Long projectId = 1L;
        String owner = "owner";
        String repository = "repo";
        long pullRequestNumber = 1L;

        GitHubPullRequestResponse pullRequest =
            new GitHubPullRequestResponse();

        pullRequest.setNumber(pullRequestNumber);
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

        ChangeSnapshot snapshot =
            new ChangeSnapshot();

        snapshot.setPullRequestNumber(pullRequestNumber);
        snapshot.setOwner(owner);
        snapshot.setRepository(repository);
        snapshot.setTitle("Test PR");

        Source source = mock(Source.class);

        when(source.getId()).thenReturn(10L);

        Change change = mock(Change.class);

        when(change.getId()).thenReturn(20L);

        Finding finding =
            new Finding(
                AnalyzerType.CODE,
                FindingType.CODE_ISSUE,
                FindingSeverity.MEDIUM,
                "CODE-001",
                "Test finding",
                "Test message",
                "Test.java",
                10
            );

        when(
            sourceService.getGitHubSource(
                projectId,
                owner,
                repository
            )
        ).thenReturn(source);

        when(
            githubRestAdapter.getPullRequest(
                owner,
                repository,
                pullRequestNumber
            )
        ).thenReturn(pullRequest);

        when(
            githubRestAdapter.getPullRequestFiles(
                owner,
                repository,
                pullRequestNumber
            )
        ).thenReturn(
            List.<GitHubPullRequestFileResponse>of()
        );

        when(
            snapshotMapper.map(
                eq(owner),
                eq(repository),
                eq(pullRequest),
                any()
            )
        ).thenReturn(snapshot);

        when(
            changeService.getOrCreateChange(
                eq(source.getId()),
                eq(String.valueOf(pullRequestNumber)),
                eq(snapshot.getTitle()),
                eq("test-user"),
                eq("base-sha"),
                eq("head-sha"),
                eq("open")
            )
        ).thenReturn(change);

        when(
            analyzerEngine.analyze(
                any(AnalyzerContext.class)
            )
        ).thenReturn(
            List.of(finding)
        );

        MlPredictionResponse prediction =
            new MlPredictionResponse();

        prediction.setRiskLevel("MEDIUM");
        prediction.setRiskScore(50.0);
        prediction.setModelName("xgboost_candidate");
        prediction.setModelVersion("1.0.0");
        prediction.setFeatureVersion("1.0.0");
        prediction.setDatasetVersion("1.0.0");

        when(
            mlPredictionClient.predict(
                eq(snapshot),
                eq(List.of(finding))
            )
        ).thenReturn(prediction);

        AnalyzePullRequestResponse response =
            analysisService.analyzePullRequest(
                projectId,
                owner,
                repository,
                pullRequestNumber
            );

        assertSame(
            snapshot,
            response.getSnapshot()
        );

        assertSame(
            change.getId(),
            response.getChangeId()
        );

        assertEquals(
            List.of(finding),
            response.getFindings()
        );

        ArgumentCaptor<AnalyzerContext> contextCaptor =
            ArgumentCaptor.forClass(
                AnalyzerContext.class
            );

        verify(analyzerEngine)
            .analyze(
                contextCaptor.capture()
            );

        assertSame(
            snapshot,
            contextCaptor
                .getValue()
                .changeSnapshot()
        );

        verify(findingPersistenceService)
            .replaceFindings(
                change,
                List.of(finding)
            );

        verify(mlPredictionClient)
            .predict(
                snapshot,
                List.of(finding)
            );

        verify(mlPredictionPersistenceService)
            .save(
                change,
                prediction
            );
    }
}
