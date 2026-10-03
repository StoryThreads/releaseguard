package com.releaseguard.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.dto.analysis.AnalysisStatusResponse;
import com.releaseguard.dto.analysis.ChangeAnalysisDetailsResponse;
import com.releaseguard.dto.analysis.DetailedFindingResponse;
import com.releaseguard.dto.analysis.DetailedPredictionResponse;
import com.releaseguard.dto.change.ChangeResponse;
import com.releaseguard.dto.project.ProjectResponse;
import com.releaseguard.dto.project.ProjectSummaryResponse;
import com.releaseguard.dto.source.SourceResponse;
import com.releaseguard.entity.*;
import com.releaseguard.exception.ResourceNotFoundException;
import com.releaseguard.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class DashboardService {

    private static final Logger log = LoggerFactory.getLogger(DashboardService.class);

    private final ProjectRepository projectRepository;
    private final SourceRepository sourceRepository;
    private final ChangeRepository changeRepository;
    private final FindingRepository findingRepository;
    private final MlPredictionRepository mlPredictionRepository;
    private final ObjectMapper objectMapper;
    private final com.releaseguard.github.GitHubRestAdapter gitHubRestAdapter;

    public DashboardService(
        ProjectRepository projectRepository,
        SourceRepository sourceRepository,
        ChangeRepository changeRepository,
        FindingRepository findingRepository,
        MlPredictionRepository mlPredictionRepository,
        ObjectMapper objectMapper,
        @org.springframework.beans.factory.annotation.Autowired(required = false)
        com.releaseguard.github.GitHubRestAdapter gitHubRestAdapter
    ) {
        this.projectRepository = projectRepository;
        this.sourceRepository = sourceRepository;
        this.changeRepository = changeRepository;
        this.findingRepository = findingRepository;
        this.mlPredictionRepository = mlPredictionRepository;
        this.objectMapper = objectMapper;
        this.gitHubRestAdapter = gitHubRestAdapter;
    }

    public ChangeAnalysisDetailsResponse getChangeAnalysisDetails(Long changeId) {
        Change change = changeRepository.findById(changeId)
            .orElseThrow(() -> new ResourceNotFoundException("Change not found with id: " + changeId));

        List<com.releaseguard.dto.analysis.ChangedFileResponse> files = fetchChangedFiles(change);
        return buildChangeAnalysisDetails(change, files);
    }

    public List<ChangeAnalysisDetailsResponse> getRecentChanges(int limit) {
        List<Change> changes = changeRepository.findAllByOrderByCreatedAtDesc();
        if (limit > 0 && changes.size() > limit) {
            changes = changes.subList(0, limit);
        }

        return changes.stream()
            .map(this::buildChangeAnalysisDetails)
            .toList();
    }

    public List<ChangeAnalysisDetailsResponse> getChangesByProject(Long projectId) {
        return changeRepository.findBySourceProjectIdOrderByCreatedAtDesc(projectId)
            .stream()
            .map(this::buildChangeAnalysisDetails)
            .toList();
    }

    public ProjectSummaryResponse getProjectSummary(Long projectId) {
        Project project = projectRepository.findById(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("Project not found with id: " + projectId));

        List<Source> sources = sourceRepository.findByProjectId(projectId);
        List<Change> changes = changeRepository.findBySourceProjectIdOrderByCreatedAtDesc(projectId);

        Map<String, Long> riskCounts = new HashMap<>();
        riskCounts.put("LOW", 0L);
        riskCounts.put("MEDIUM", 0L);
        riskCounts.put("HIGH", 0L);
        riskCounts.put("CRITICAL", 0L);

        double totalScore = 0.0;
        int scoredCount = 0;

        List<ChangeAnalysisDetailsResponse> detailedChanges = new ArrayList<>();

        for (Change change : changes) {
            ChangeAnalysisDetailsResponse details = buildChangeAnalysisDetails(change);
            detailedChanges.add(details);

            if (details.getPrediction() != null) {
                String level = details.getPrediction().getRiskLevel();
                if (level != null) {
                    riskCounts.put(level, riskCounts.getOrDefault(level, 0L) + 1L);
                }
                totalScore += details.getPrediction().getRiskScore();
                scoredCount++;
            }
        }

        double averageRiskScore = scoredCount > 0 ? (totalScore / scoredCount) : 0.0;

        ProjectResponse projectResponse = new ProjectResponse(
            project.getId(),
            project.getName(),
            project.getDescription(),
            project.getCreatedAt(),
            project.getUpdatedAt()
        );

        return new ProjectSummaryResponse(
            projectResponse,
            sources.size(),
            changes.size(),
            riskCounts,
            Math.round(averageRiskScore * 1000.0) / 1000.0,
            detailedChanges
        );
    }

    public AnalysisStatusResponse getAnalysisStatus(Long changeId) {
        Change change = changeRepository.findById(changeId)
            .orElseThrow(() -> new ResourceNotFoundException("Change not found with id: " + changeId));

        Optional<MlPredictionEntity> prediction = mlPredictionRepository.findByChangeId(changeId);
        long findingsCount = findingRepository.countByChangeId(changeId);

        if (prediction.isPresent()) {
            MlPredictionEntity p = prediction.get();
            return new AnalysisStatusResponse(
                changeId,
                UUID.randomUUID().toString(),
                "COMPLETED",
                "Analysis complete and persisted",
                "Analysis completed with " + findingsCount + " findings and risk level " + p.getRiskLevel(),
                findingsCount,
                p.getRiskLevel(),
                p.getRiskScore()
            );
        } else {
            return new AnalysisStatusResponse(
                changeId,
                UUID.randomUUID().toString(),
                "IN_PROGRESS",
                "Analyzing change snapshot and generating ML risk prediction",
                "Analysis in progress",
                findingsCount,
                "UNKNOWN",
                0.0
            );
        }
    }

    private ChangeAnalysisDetailsResponse buildChangeAnalysisDetails(Change change) {
        return buildChangeAnalysisDetails(change, List.of());
    }

    private ChangeAnalysisDetailsResponse buildChangeAnalysisDetails(
        Change change,
        List<com.releaseguard.dto.analysis.ChangedFileResponse> files
    ) {
        ChangeResponse changeResponse = new ChangeResponse(
            change.getId(),
            change.getSource().getId(),
            change.getExternalChangeId(),
            change.getTitle(),
            change.getAuthor(),
            change.getBaseRevision(),
            change.getHeadRevision(),
            change.getStatus(),
            change.getCreatedAt(),
            change.getUpdatedAt()
        );

        Source source = change.getSource();
        SourceResponse sourceResponse = new SourceResponse(
            source.getId(),
            source.getProject().getId(),
            source.getProvider(),
            source.getRepositoryOwner(),
            source.getRepositoryName(),
            source.getDefaultBranch(),
            source.getCreatedAt(),
            source.getUpdatedAt()
        );

        // Fetch findings
        List<FindingEntity> findingEntities = findingRepository.findByChangeIdOrderByIdAsc(change.getId());
        List<DetailedFindingResponse> findings = findingEntities.stream()
            .map(f -> new DetailedFindingResponse(
                f.getId(),
                f.getAnalyzerType(),
                f.getFindingType(),
                f.getSeverity(),
                f.getRuleId(),
                f.getTitle(),
                f.getMessage(),
                f.getFilePath(),
                f.getLineNumber(),
                f.getCreatedAt()
            ))
            .toList();

        Map<String, Long> severityCounts = findingEntities.stream()
            .collect(Collectors.groupingBy(FindingEntity::getSeverity, Collectors.counting()));

        // Fetch prediction
        DetailedPredictionResponse predictionResponse = null;
        Optional<MlPredictionEntity> predictionOpt = mlPredictionRepository.findByChangeId(change.getId());
        if (predictionOpt.isPresent()) {
            MlPredictionEntity entity = predictionOpt.get();
            Map<String, Double> probs = parseClassProbabilities(entity.getClassProbabilities());
            Map<String, Object> featureVector = parseFeatureVector(entity.getFeatureVector());

            predictionResponse = new DetailedPredictionResponse(
                entity.getRiskLevel(),
                entity.getRiskScore(),
                probs,
                featureVector,
                entity.getModelName(),
                entity.getModelVersion(),
                entity.getFeatureVersion(),
                entity.getDatasetVersion(),
                entity.getCreatedAt()
            );
        }

        return new ChangeAnalysisDetailsResponse(
            changeResponse,
            sourceResponse,
            predictionResponse,
            findings,
            severityCounts,
            files
        );
    }

    private List<com.releaseguard.dto.analysis.ChangedFileResponse> fetchChangedFiles(Change change) {
        if (gitHubRestAdapter == null || change == null || change.getSource() == null) {
            return List.of();
        }
        Source source = change.getSource();
        if (!"GITHUB".equalsIgnoreCase(source.getProvider())) {
            return List.of();
        }
        try {
            long prNumber = Long.parseLong(change.getExternalChangeId());
            var ghFiles = gitHubRestAdapter.getPullRequestFiles(
                source.getRepositoryOwner(),
                source.getRepositoryName(),
                prNumber
            );
            if (ghFiles == null || ghFiles.isEmpty()) {
                return List.of();
            }
            List<com.releaseguard.dto.analysis.ChangedFileResponse> result = new ArrayList<>();
            for (var f : ghFiles) {
                List<String> tags = new ArrayList<>();
                String fn = f.getFilename() != null ? f.getFilename().toLowerCase() : "";
                if (fn.contains("test")) tags.add("TEST");
                if (fn.endsWith(".md") || fn.contains("doc")) tags.add("DOCS");
                if (fn.endsWith(".yml") || fn.endsWith(".yaml") || fn.endsWith(".json") || fn.endsWith(".properties")) tags.add("CONFIG");
                if (f.getChanges() > 100) tags.add("HIGH-CHURN");

                result.add(new com.releaseguard.dto.analysis.ChangedFileResponse(
                    f.getFilename(),
                    f.getStatus(),
                    f.getAdditions(),
                    f.getDeletions(),
                    f.getChanges(),
                    f.getPatch(),
                    tags
                ));
            }
            return result;
        } catch (Exception e) {
            log.debug("Could not fetch changed files from GitHub for change {}: {}", change.getId(), e.getMessage());
            return List.of();
        }
    }

    private Map<String, Double> parseClassProbabilities(String json) {
        if (json == null || json.isBlank()) {
            return Collections.emptyMap();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Double>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse class probabilities JSON: {}", json);
            return Collections.emptyMap();
        }
    }

    private Map<String, Object> parseFeatureVector(String json) {
        if (json == null || json.isBlank()) {
            return Collections.emptyMap();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse feature vector JSON: {}", json);
            return Collections.emptyMap();
        }
    }
}
