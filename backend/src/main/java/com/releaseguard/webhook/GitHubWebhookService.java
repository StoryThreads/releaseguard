package com.releaseguard.webhook;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.entity.ProcessedEvent;
import com.releaseguard.entity.Project;
import com.releaseguard.entity.Source;
import com.releaseguard.kafka.AnalysisEventProducer;
import com.releaseguard.repository.ProcessedEventRepository;
import com.releaseguard.repository.ProjectRepository;
import com.releaseguard.repository.SourceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class GitHubWebhookService {

    private static final Logger log = LoggerFactory.getLogger(GitHubWebhookService.class);

    private static final Set<String> SUPPORTED_PR_ACTIONS = Set.of(
        "opened",
        "synchronize",
        "reopened",
        "edited"
    );

    private final ProcessedEventRepository processedEventRepository;
    private final ProjectRepository projectRepository;
    private final SourceRepository sourceRepository;
    private final AnalysisService analysisService;
    private final AnalysisEventProducer analysisEventProducer;

    // In-memory cache for fast delivery deduplication and status lookup
    private final Map<String, String> deliveryStatusCache = new ConcurrentHashMap<>();

    public GitHubWebhookService(
        ProcessedEventRepository processedEventRepository,
        ProjectRepository projectRepository,
        SourceRepository sourceRepository,
        AnalysisService analysisService,
        AnalysisEventProducer analysisEventProducer
    ) {
        this.processedEventRepository = processedEventRepository;
        this.projectRepository = projectRepository;
        this.sourceRepository = sourceRepository;
        this.analysisService = analysisService;
        this.analysisEventProducer = analysisEventProducer;
    }

    public boolean isDuplicateDelivery(String deliveryId) {
        if (deliveryId == null || deliveryId.isBlank()) {
            return false;
        }

        if (deliveryStatusCache.containsKey(deliveryId)) {
            return true;
        }

        return processedEventRepository.existsById(deliveryId);
    }

    @Transactional
    public WebhookProcessingResult processPullRequestWebhook(
        String deliveryId,
        GitHubWebhookDto payload
    ) {
        String effectiveDeliveryId = (deliveryId != null && !deliveryId.isBlank())
            ? deliveryId
            : UUID.randomUUID().toString();

        String correlationId = UUID.randomUUID().toString();

        if (isDuplicateDelivery(effectiveDeliveryId)) {
            log.info("Duplicate GitHub delivery ID: {} ignored", effectiveDeliveryId);
            return new WebhookProcessingResult(
                effectiveDeliveryId,
                correlationId,
                "DUPLICATE_IGNORED",
                "Duplicate webhook delivery detected and safely ignored",
                null,
                null
            );
        }

        // Record processed event to prevent duplicate processing
        ProcessedEvent processedEvent = new ProcessedEvent(
            effectiveDeliveryId,
            "github.pull_request." + payload.getAction(),
            correlationId
        );
        processedEventRepository.save(processedEvent);
        deliveryStatusCache.put(effectiveDeliveryId, "PROCESSING");

        String action = payload.getAction();
        if (action == null || !SUPPORTED_PR_ACTIONS.contains(action.toLowerCase())) {
            log.info("Ignored PR action: {} for delivery ID: {}", action, effectiveDeliveryId);
            processedEvent.markCompleted();
            processedEventRepository.save(processedEvent);
            deliveryStatusCache.put(effectiveDeliveryId, "COMPLETED");

            return new WebhookProcessingResult(
                effectiveDeliveryId,
                correlationId,
                "ACTION_SKIPPED",
                "PR action '" + action + "' does not require analysis",
                null,
                null
            );
        }

        // Extract repository owner and name
        String owner;
        String repoName;

        if (payload.getRepository() != null) {
            repoName = payload.getRepository().getName();
            if (payload.getRepository().getOwner() != null && payload.getRepository().getOwner().getLogin() != null) {
                owner = payload.getRepository().getOwner().getLogin();
            } else if (payload.getRepository().getFullName() != null && payload.getRepository().getFullName().contains("/")) {
                owner = payload.getRepository().getFullName().split("/")[0];
            } else {
                owner = "unknown";
            }
        } else {
            owner = "unknown";
            repoName = "unknown";
        }

        Long prNumber = payload.getNumber();
        if (prNumber == null && payload.getPullRequest() != null) {
            prNumber = payload.getPullRequest().getNumber();
        }

        if (prNumber == null) {
            log.warn("Missing PR number in webhook payload for delivery {}", effectiveDeliveryId);
            processedEvent.markCompleted();
            processedEventRepository.save(processedEvent);
            return new WebhookProcessingResult(
                effectiveDeliveryId,
                correlationId,
                "FAILED",
                "Missing pull request number in webhook",
                null,
                null
            );
        }

        // Find or auto-provision Source & Project
        Source source = findOrProvisionSource(owner, repoName);

        // Publish Kafka analysis event
        try {
            analysisEventProducer.publishAnalysisRequest(
                source.getProject().getId(),
                owner,
                repoName,
                prNumber,
                correlationId
            );
            log.info("Published Kafka analysis event for {}/{}#{} (Correlation: {})", owner, repoName, prNumber, correlationId);
        } catch (Exception kafkaEx) {
            log.warn("Could not publish Kafka event (will proceed directly): {}", kafkaEx.getMessage());
        }

        // Run automated analysis & result persistence
        AnalyzePullRequestResponse analysisResponse = null;
        try {
            analysisResponse = analysisService.analyzePullRequest(
                source.getProject().getId(),
                owner,
                repoName,
                prNumber
            );
            log.info("Completed automated analysis for {}/{}#{} - Change ID: {}", owner, repoName, prNumber, analysisResponse.getChangeId());

            processedEvent.markCompleted();
            processedEventRepository.save(processedEvent);
            deliveryStatusCache.put(effectiveDeliveryId, "COMPLETED");

            return new WebhookProcessingResult(
                effectiveDeliveryId,
                correlationId,
                "COMPLETED",
                "Automated analysis completed successfully for PR #" + prNumber,
                analysisResponse.getChangeId(),
                analysisResponse
            );
        } catch (Exception ex) {
            log.error("Automated analysis execution failed for {}/{}#{}: {}", owner, repoName, prNumber, ex.getMessage(), ex);
            deliveryStatusCache.put(effectiveDeliveryId, "FAILED");

            return new WebhookProcessingResult(
                effectiveDeliveryId,
                correlationId,
                "ANALYSIS_QUEUED",
                "Webhook accepted and analysis queued: " + ex.getMessage(),
                null,
                null
            );
        }
    }

    private Source findOrProvisionSource(String owner, String repoName) {
        List<Source> sources = sourceRepository
            .findByProviderIgnoreCaseAndRepositoryOwnerIgnoreCaseAndRepositoryNameIgnoreCase(
                "GITHUB",
                owner,
                repoName
            );

        if (!sources.isEmpty()) {
            return sources.get(0);
        }

        // Auto-provision Project and Source if not yet configured
        String projectName = owner + "/" + repoName;
        Project project = new Project();
        project.setName(projectName);
        project.setDescription("Auto-configured project for " + projectName);
        project = projectRepository.save(project);

        Source newSource = new Source();
        newSource.setProject(project);
        newSource.setProvider("GITHUB");
        newSource.setRepositoryOwner(owner);
        newSource.setRepositoryName(repoName);
        newSource.setDefaultBranch("main");
        return sourceRepository.save(newSource);
    }

    public static class WebhookProcessingResult {
        private final String deliveryId;
        private final String correlationId;
        private final String status;
        private final String message;
        private final Long changeId;
        private final AnalyzePullRequestResponse analysisResponse;

        public WebhookProcessingResult(
            String deliveryId,
            String correlationId,
            String status,
            String message,
            Long changeId,
            AnalyzePullRequestResponse analysisResponse
        ) {
            this.deliveryId = deliveryId;
            this.correlationId = correlationId;
            this.status = status;
            this.message = message;
            this.changeId = changeId;
            this.analysisResponse = analysisResponse;
        }

        public String getDeliveryId() {
            return deliveryId;
        }

        public String getCorrelationId() {
            return correlationId;
        }

        public String getStatus() {
            return status;
        }

        public String getMessage() {
            return message;
        }

        public Long getChangeId() {
            return changeId;
        }

        public AnalyzePullRequestResponse getAnalysisResponse() {
            return analysisResponse;
        }
    }
}
