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

    @Mock
    private com.releaseguard.redis.RedisCacheService redisCacheService;

    @org.mockito.Spy
    private com.releaseguard.redis.RedisProperties redisProperties =
            new com.releaseguard.redis.RedisProperties();

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

    @Test
    @SuppressWarnings("unchecked")
    void shouldUseCachedGitHubFilesAndMlPredictionWhenPresentInRedis() {
        Long projectId = 1L;
        String owner = "owner";
        String repository = "repo";
        long pullRequestNumber = 1L;

        GitHubPullRequestResponse pullRequest = new GitHubPullRequestResponse();
        pullRequest.setNumber(pullRequestNumber);
        pullRequest.setTitle("Test PR");
        pullRequest.setState("open");

        GitHubPullRequestResponse.User user = new GitHubPullRequestResponse.User();
        user.setLogin("test-user");
        pullRequest.setUser(user);

        GitHubPullRequestResponse.Branch base = new GitHubPullRequestResponse.Branch();
        base.setSha("base-sha");
        pullRequest.setBase(base);

        GitHubPullRequestResponse.Branch head = new GitHubPullRequestResponse.Branch();
        head.setSha("head-sha-cached");
        pullRequest.setHead(head);

        when(githubRestAdapter.getPullRequest(owner, repository, pullRequestNumber))
                .thenReturn(pullRequest);

        Source source = mock(Source.class);
        when(source.getId()).thenReturn(10L);
        when(sourceService.getGitHubSource(projectId, owner, repository)).thenReturn(source);

        GitHubPullRequestFileResponse cachedFile = new GitHubPullRequestFileResponse();
        cachedFile.setFilename("CachedService.java");
        List<GitHubPullRequestFileResponse> cachedFiles = List.of(cachedFile);

        // Redis has cached files for this commit SHA
        when(redisCacheService.get(
                eq(com.releaseguard.redis.RedisKeys.gitHubFiles(owner, repository, "head-sha-cached")),
                any(com.fasterxml.jackson.core.type.TypeReference.class)
        )).thenReturn(java.util.Optional.of(cachedFiles));

        ChangeSnapshot snapshot = new ChangeSnapshot();
        snapshot.setPullRequestNumber(pullRequestNumber);
        snapshot.setOwner(owner);
        snapshot.setRepository(repository);
        snapshot.setTitle("Test PR");

        when(snapshotMapper.map(owner, repository, pullRequest, cachedFiles)).thenReturn(snapshot);

        Change change = mock(Change.class);
        when(change.getId()).thenReturn(20L);
        when(changeService.getOrCreateChange(
                eq(10L), eq("1"), eq("Test PR"), eq("test-user"),
                eq("base-sha"), eq("head-sha-cached"), eq("open")
        )).thenReturn(change);

        when(analyzerEngine.analyze(any(AnalyzerContext.class))).thenReturn(List.of());

        MlPredictionResponse cachedPrediction = new MlPredictionResponse();
        cachedPrediction.setRiskLevel("LOW");
        cachedPrediction.setRiskScore(12.5);
        cachedPrediction.setModelVersion("2.0.0");
        cachedPrediction.setModelName("xgboost");
        cachedPrediction.setClassProbabilities(java.util.Map.of("LOW", 0.95));
        cachedPrediction.setFeatureVector(java.util.Map.of("churn", 5.0));
        cachedPrediction.setFeatureVersion("1.0.0");
        cachedPrediction.setDatasetVersion("2.0.0");

        when(mlPredictionClient.getActiveModelVersion()).thenReturn("2.0.0");

        // Redis has cached prediction for this commit SHA
        when(redisCacheService.get(
                eq(com.releaseguard.redis.RedisKeys.predictionResult("head-sha-cached", "2.0.0")),
                eq(MlPredictionResponse.class)
        )).thenReturn(java.util.Optional.of(cachedPrediction));

        AnalyzePullRequestResponse response = analysisService.analyzePullRequest(
                projectId, owner, repository, pullRequestNumber
        );

        // Assert: External GitHub PR files call was SKIPPED due to Redis cache
        verify(githubRestAdapter, never()).getPullRequestFiles(anyString(), anyString(), anyLong());

        // Assert: External ML prediction service call was SKIPPED due to Redis cache
        verify(mlPredictionClient, never()).predict(any(), any());

        // Assert: PostgreSQL authoritative persistence still occurred
        verify(findingPersistenceService).replaceFindings(eq(change), eq(List.of()));
        verify(mlPredictionPersistenceService).save(eq(change), eq(cachedPrediction));

        assertSame(snapshot, response.getSnapshot());
        assertSame(cachedPrediction, response.getRiskAnalysis());
    }

    @Test
    void shouldRespectConfiguredActiveModelVersionInPredictionCacheKey() {
        Long projectId = 10L;
        String owner = "test-owner";
        String repository = "test-repo";
        long pullRequestNumber = 42L;

        GitHubPullRequestResponse pullRequest = new GitHubPullRequestResponse();
        pullRequest.setNumber(pullRequestNumber);
        pullRequest.setTitle("Upgrade Model PR");
        pullRequest.setState("open");

        GitHubPullRequestResponse.Branch head = new GitHubPullRequestResponse.Branch();
        head.setSha("sha-v21");
        pullRequest.setHead(head);

        GitHubPullRequestResponse.Branch base = new GitHubPullRequestResponse.Branch();
        base.setSha("base-sha");
        pullRequest.setBase(base);

        GitHubPullRequestResponse.User user = new GitHubPullRequestResponse.User();
        user.setLogin("test-user");
        pullRequest.setUser(user);

        when(githubRestAdapter.getPullRequest(owner, repository, pullRequestNumber)).thenReturn(pullRequest);
        when(githubRestAdapter.getPullRequestFiles(owner, repository, pullRequestNumber)).thenReturn(List.of());

        Source source = mock(Source.class);
        when(source.getId()).thenReturn(10L);
        when(sourceService.getGitHubSource(projectId, owner, repository)).thenReturn(source);

        ChangeSnapshot snapshot = new ChangeSnapshot();
        snapshot.setPullRequestNumber(pullRequestNumber);
        snapshot.setTitle("Upgrade Model PR");
        when(snapshotMapper.map(eq(owner), eq(repository), eq(pullRequest), any())).thenReturn(snapshot);

        Change change = mock(Change.class);
        when(change.getId()).thenReturn(55L);
        when(changeService.getOrCreateChange(
                eq(10L), eq("42"), eq("Upgrade Model PR"), eq("test-user"),
                eq("base-sha"), eq("sha-v21"), eq("open")
        )).thenReturn(change);
        when(analyzerEngine.analyze(any())).thenReturn(List.of());

        // Configure active model version to 2.1.0 dynamically
        when(mlPredictionClient.getActiveModelVersion()).thenReturn("2.1.0");

        MlPredictionResponse prediction = new MlPredictionResponse();
        prediction.setModelVersion("2.1.0");
        prediction.setRiskLevel("LOW");
        prediction.setRiskScore(10.0);
        when(mlPredictionClient.predict(any(), any())).thenReturn(prediction);

        analysisService.analyzePullRequest(projectId, owner, repository, pullRequestNumber);

        // Verify lookup checked prediction:sha-v21:2.1.0 (not hardcoded 2.0.0)
        verify(redisCacheService).get(
                eq(com.releaseguard.redis.RedisKeys.predictionResult("sha-v21", "2.1.0")),
                eq(MlPredictionResponse.class)
        );

        // Verify storage stored prediction:sha-v21:2.1.0
        verify(redisCacheService).put(
                eq(com.releaseguard.redis.RedisKeys.predictionResult("sha-v21", "2.1.0")),
                eq(prediction),
                any()
        );
    }
}
