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
import com.releaseguard.ml.MlPredictionClient;
import com.releaseguard.ml.dto.MlPredictionResponse;
import com.releaseguard.service.ChangeService;
import com.releaseguard.service.FindingPersistenceService;
import com.releaseguard.service.MlPredictionPersistenceService;
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
    private final MlPredictionClient mlPredictionClient;
    private final MlPredictionPersistenceService mlPredictionPersistenceService;
    private final com.releaseguard.redis.RedisCacheService redisCacheService;
    private final com.releaseguard.redis.RedisProperties redisProperties;

    public AnalysisService(
        GitHubRestAdapter githubRestAdapter,
        GitHubChangeSnapshotMapper snapshotMapper,
        SourceService sourceService,
        ChangeService changeService,
        AnalyzerEngine analyzerEngine,
        FindingPersistenceService findingPersistenceService,
        MlPredictionClient mlPredictionClient,
        MlPredictionPersistenceService mlPredictionPersistenceService
    ) {
        this(
            githubRestAdapter,
            snapshotMapper,
            sourceService,
            changeService,
            analyzerEngine,
            findingPersistenceService,
            mlPredictionClient,
            mlPredictionPersistenceService,
            null,
            new com.releaseguard.redis.RedisProperties()
        );
    }

    @org.springframework.beans.factory.annotation.Autowired
    public AnalysisService(
        GitHubRestAdapter githubRestAdapter,
        GitHubChangeSnapshotMapper snapshotMapper,
        SourceService sourceService,
        ChangeService changeService,
        AnalyzerEngine analyzerEngine,
        FindingPersistenceService findingPersistenceService,
        MlPredictionClient mlPredictionClient,
        MlPredictionPersistenceService mlPredictionPersistenceService,
        @org.springframework.lang.Nullable
        com.releaseguard.redis.RedisCacheService redisCacheService,
        @org.springframework.lang.Nullable
        com.releaseguard.redis.RedisProperties redisProperties
    ) {
        this.githubRestAdapter = githubRestAdapter;
        this.snapshotMapper = snapshotMapper;
        this.sourceService = sourceService;
        this.changeService = changeService;
        this.analyzerEngine = analyzerEngine;
        this.findingPersistenceService = findingPersistenceService;
        this.mlPredictionClient = mlPredictionClient;
        this.mlPredictionPersistenceService = mlPredictionPersistenceService;
        this.redisCacheService = redisCacheService;
        this.redisProperties = redisProperties != null ? redisProperties : new com.releaseguard.redis.RedisProperties();
    }

    @Transactional
    public AnalyzePullRequestResponse analyzePullRequest(
        Long projectId,
        String owner,
        String repository,
        long pullRequestNumber
    ) {

        Source source =
            sourceService.getGitHubSource(
                projectId,
                owner,
                repository
            );

        GitHubPullRequestResponse pullRequest =
            githubRestAdapter.getPullRequest(
                owner,
                repository,
                pullRequestNumber
            );

        String headRevision =
            pullRequest.getHead() != null
                ? pullRequest.getHead().getSha()
                : "unknown";

        List<GitHubPullRequestFileResponse> files = null;
        String filesCacheKey = !"unknown".equals(headRevision)
            ? com.releaseguard.redis.RedisKeys.gitHubFiles(owner, repository, headRevision)
            : null;

        if (redisCacheService != null && filesCacheKey != null) {
            files = redisCacheService.get(
                filesCacheKey,
                new com.fasterxml.jackson.core.type.TypeReference<List<GitHubPullRequestFileResponse>>() {}
            ).orElse(null);
        }

        if (files == null) {
            files = githubRestAdapter.getPullRequestFiles(
                owner,
                repository,
                pullRequestNumber
            );
            if (redisCacheService != null && filesCacheKey != null && files != null) {
                redisCacheService.put(
                    filesCacheKey,
                    files,
                    java.time.Duration.ofSeconds(redisProperties.getTtls().getGithubDiffSeconds())
                );
            }
        }

        ChangeSnapshot snapshot =
            snapshotMapper.map(
                owner,
                repository,
                pullRequest,
                files
            );

        String author =
            pullRequest.getUser() != null
                ? pullRequest.getUser().getLogin()
                : "unknown";

        String baseRevision =
            pullRequest.getBase() != null
                ? pullRequest.getBase().getSha()
                : "unknown";

        String status =
            pullRequest.getState() != null
                ? pullRequest.getState()
                : "unknown";

        Change change =
            changeService.getOrCreateChange(
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

        String configuredModelVersion = (mlPredictionClient != null)
            ? mlPredictionClient.getActiveModelVersion()
            : null;
        String activeModelVersion = (configuredModelVersion != null && !configuredModelVersion.isBlank())
            ? configuredModelVersion
            : "2.0.0";

        MlPredictionResponse riskAnalysis = null;
        String predictionCacheKey = !"unknown".equals(headRevision)
            ? com.releaseguard.redis.RedisKeys.predictionResult(headRevision, activeModelVersion)
            : null;

        if (redisCacheService != null && predictionCacheKey != null) {
            riskAnalysis = redisCacheService.get(
                predictionCacheKey,
                MlPredictionResponse.class
            ).orElse(null);
        }

        if (riskAnalysis == null) {
            riskAnalysis = mlPredictionClient.predict(
                snapshot,
                findings
            );
            if (redisCacheService != null && riskAnalysis != null && !"unknown".equals(headRevision)) {
                String modelVersion = (riskAnalysis.getModelVersion() != null && !riskAnalysis.getModelVersion().isBlank())
                    ? riskAnalysis.getModelVersion()
                    : activeModelVersion;
                String versionedKey = com.releaseguard.redis.RedisKeys.predictionResult(headRevision, modelVersion);
                redisCacheService.put(
                    versionedKey,
                    riskAnalysis,
                    java.time.Duration.ofSeconds(redisProperties.getTtls().getPredictionResultSeconds())
                );
            }
        }

        mlPredictionPersistenceService.save(
            change,
            riskAnalysis
        );

        return new AnalyzePullRequestResponse(
            snapshot,
            change.getId(),
            findings,
            riskAnalysis
        );
    }
}
