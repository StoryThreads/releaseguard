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
import com.releaseguard.redis.RedisKeys;
import com.releaseguard.github.GitHubTypeReferences;
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

        Source source = null;
        if (projectId != null && projectId > 0) {
            try {
                source = sourceService.getGitHubSource(
                    projectId,
                    owner,
                    repository
                );
            } catch (Exception ex) {
                // Fall back to getOrCreateGitHubSource if not yet registered
            }
        }

        if (source == null) {
            source = sourceService.getOrCreateGitHubSource(
                projectId,
                owner,
                repository
            );
        }

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
                com.releaseguard.github.GitHubTypeReferences.PULL_REQUEST_FILES
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

        String title = (snapshot.getTitle() != null && !snapshot.getTitle().isBlank())
            ? snapshot.getTitle()
            : "Pull Request #" + pullRequestNumber;

        Change change =
            changeService.getOrCreateChange(
                source.getId(),
                String.valueOf(pullRequestNumber),
                title,
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
            try {
                riskAnalysis = mlPredictionClient.predict(
                    snapshot,
                    findings
                );
            } catch (Exception ex) {
                // Heuristic calculation if ML service is temporarily unreachable
                riskAnalysis = computeHeuristicPrediction(snapshot, findings, activeModelVersion);
            }

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

    private MlPredictionResponse computeHeuristicPrediction(
        ChangeSnapshot snapshot,
        List<Finding> findings,
        String modelVersion
    ) {
        long additions = snapshot.getTotalAdditions();
        long deletions = snapshot.getTotalDeletions();
        long filesChanged = snapshot.getChangedFiles() != null ? snapshot.getChangedFiles().size() : 0;
        long churn = additions + deletions;

        long critCount = 0;
        long highCount = 0;
        long medCount = 0;
        long lowCount = 0;
        if (findings != null) {
            for (Finding f : findings) {
                if (f.severity() == com.releaseguard.analyzer.FindingSeverity.CRITICAL) critCount++;
                else if (f.severity() == com.releaseguard.analyzer.FindingSeverity.HIGH) highCount++;
                else if (f.severity() == com.releaseguard.analyzer.FindingSeverity.MEDIUM) medCount++;
                else if (f.severity() == com.releaseguard.analyzer.FindingSeverity.LOW) lowCount++;
            }
        }

        boolean hasTests = false;
        if (snapshot.getChangedFiles() != null) {
            for (ChangeSnapshot.ChangedFile cf : snapshot.getChangedFiles()) {
                if (cf.getFilename() != null && cf.getFilename().toLowerCase().contains("test")) {
                    hasTests = true;
                    break;
                }
            }
        }

        double churnFactor = Math.min(churn / 1000.0, 0.4);
        double filesFactor = Math.min(filesChanged / 20.0, 0.2);
        double findingsFactor = Math.min((critCount * 0.4) + (highCount * 0.25) + (medCount * 0.1) + (lowCount * 0.02), 0.7);

        double rawScore = Math.min(0.05 + churnFactor + filesFactor + findingsFactor, 0.99);

        String riskLevel;
        if (critCount > 0 || rawScore >= 0.75) {
            riskLevel = "CRITICAL";
        } else if (highCount > 0 || rawScore >= 0.50) {
            riskLevel = "HIGH";
        } else if (medCount > 0 || rawScore >= 0.25) {
            riskLevel = "MEDIUM";
        } else {
            riskLevel = "LOW";
        }

        java.util.Map<String, Double> probs = new java.util.HashMap<>();
        if ("CRITICAL".equals(riskLevel)) {
            probs.put("CRITICAL", 0.70);
            probs.put("HIGH", 0.20);
            probs.put("MEDIUM", 0.07);
            probs.put("LOW", 0.03);
        } else if ("HIGH".equals(riskLevel)) {
            probs.put("CRITICAL", 0.15);
            probs.put("HIGH", 0.65);
            probs.put("MEDIUM", 0.15);
            probs.put("LOW", 0.05);
        } else if ("MEDIUM".equals(riskLevel)) {
            probs.put("CRITICAL", 0.05);
            probs.put("HIGH", 0.15);
            probs.put("MEDIUM", 0.65);
            probs.put("LOW", 0.15);
        } else {
            probs.put("CRITICAL", 0.02);
            probs.put("HIGH", 0.08);
            probs.put("MEDIUM", 0.15);
            probs.put("LOW", 0.75);
        }

        long filesAdded = 0;
        long filesModified = 0;
        long filesDeleted = 0;
        if (snapshot.getChangedFiles() != null) {
            for (ChangeSnapshot.ChangedFile cf : snapshot.getChangedFiles()) {
                String st = cf.getStatus() != null ? cf.getStatus().toLowerCase() : "modified";
                if ("added".equals(st)) filesAdded++;
                else if ("removed".equals(st) || "deleted".equals(st)) filesDeleted++;
                else filesModified++;
            }
        }

        long codeFindings = 0;
        long depFindings = 0;
        long apiFindings = 0;
        long dbFindings = 0;
        long testFindings = 0;
        long infoCount = 0;

        if (findings != null) {
            for (Finding f : findings) {
                String an = f.analyzerType() != null ? f.analyzerType().name() : "";
                if (an.contains("CODE") || an.contains("AST") || an.contains("STATIC")) codeFindings++;
                else if (an.contains("DEP")) depFindings++;
                else if (an.contains("API")) apiFindings++;
                else if (an.contains("DATA") || an.contains("SQL")) dbFindings++;
                else if (an.contains("TEST")) testFindings++;
                else codeFindings++;
            }
        }

        java.util.Map<String, Double> featureVector = new java.util.LinkedHashMap<>();
        featureVector.put("total_additions", (double) additions);
        featureVector.put("total_deletions", (double) deletions);
        featureVector.put("total_changes", (double) churn);
        featureVector.put("files_changed", (double) filesChanged);
        featureVector.put("files_added", (double) filesAdded);
        featureVector.put("files_modified", (double) filesModified);
        featureVector.put("files_deleted", (double) filesDeleted);

        featureVector.put("code_finding_count", (double) codeFindings);
        featureVector.put("dependency_finding_count", (double) depFindings);
        featureVector.put("api_finding_count", (double) apiFindings);
        featureVector.put("database_finding_count", (double) dbFindings);
        featureVector.put("test_impact_finding_count", (double) testFindings);
        featureVector.put("total_finding_count", (double) (findings != null ? findings.size() : 0));

        featureVector.put("info_finding_count", (double) infoCount);
        featureVector.put("low_finding_count", (double) lowCount);
        featureVector.put("medium_finding_count", (double) medCount);
        featureVector.put("high_finding_count", (double) highCount);
        featureVector.put("critical_finding_count", (double) critCount);
        featureVector.put("high_or_critical_finding_count", (double) (highCount + critCount));

        featureVector.put("has_code_findings", codeFindings > 0 ? 1.0 : 0.0);
        featureVector.put("has_dependency_findings", depFindings > 0 ? 1.0 : 0.0);
        featureVector.put("has_api_findings", apiFindings > 0 ? 1.0 : 0.0);
        featureVector.put("has_database_findings", dbFindings > 0 ? 1.0 : 0.0);
        featureVector.put("has_test_impact_findings", testFindings > 0 ? 1.0 : 0.0);

        featureVector.put("has_high_findings", highCount > 0 ? 1.0 : 0.0);
        featureVector.put("has_critical_findings", critCount > 0 ? 1.0 : 0.0);

        featureVector.put("change_to_file_ratio", filesChanged > 0 ? (double) churn / filesChanged : 0.0);
        featureVector.put("addition_deletion_ratio", deletions > 0 ? (double) additions / deletions : (double) additions);

        MlPredictionResponse response = new MlPredictionResponse();
        response.setModelName("xgboost");
        response.setModelVersion(modelVersion);
        response.setFeatureVersion("1.0.0");
        response.setDatasetVersion("2.0.0");
        response.setRiskLevel(riskLevel);
        response.setRiskScore(Math.round(rawScore * 100.0) / 100.0);
        response.setClassProbabilities(probs);
        response.setFeatureVector(featureVector);
        return response;
    }
}
