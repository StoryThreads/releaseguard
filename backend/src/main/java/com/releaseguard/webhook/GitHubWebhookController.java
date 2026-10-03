package com.releaseguard.webhook;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/webhooks")
public class GitHubWebhookController {

    private static final Logger log = LoggerFactory.getLogger(GitHubWebhookController.class);

    private final WebhookSignatureVerifier signatureVerifier;
    private final GitHubWebhookService webhookService;
    private final ObjectMapper objectMapper;

    public GitHubWebhookController(
        WebhookSignatureVerifier signatureVerifier,
        GitHubWebhookService webhookService,
        ObjectMapper objectMapper
    ) {
        this.signatureVerifier = signatureVerifier;
        this.webhookService = webhookService;
        this.objectMapper = objectMapper;
    }

    @PostMapping(
        value = "/github",
        consumes = {MediaType.APPLICATION_JSON_VALUE, "*/*"}
    )
    public ResponseEntity<?> handleGitHubWebhook(
        @RequestHeader(value = "X-GitHub-Event", defaultValue = "pull_request") String eventType,
        @RequestHeader(value = "X-Hub-Signature-256", required = false) String signature,
        @RequestHeader(value = "X-GitHub-Delivery", required = false) String deliveryId,
        @RequestBody byte[] rawPayload
    ) {
        log.info("Received GitHub webhook event: {} (Delivery: {})", eventType, deliveryId);

        // 1. Signature Validation
        if (!signatureVerifier.isValid(rawPayload, signature)) {
            log.warn("Invalid webhook signature for delivery: {}", deliveryId);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of(
                    "status", "UNAUTHORIZED",
                    "message", "Invalid X-Hub-Signature-256 signature"
                ));
        }

        // 2. Handle Ping event
        if ("ping".equalsIgnoreCase(eventType)) {
            log.info("GitHub ping event received for delivery: {}", deliveryId);
            return ResponseEntity.ok(Map.of(
                "status", "PONG",
                "deliveryId", deliveryId != null ? deliveryId : "",
                "message", "ReleaseGuard GitHub webhook endpoint is operational"
            ));
        }

        // 3. Only handle pull_request events
        if (!"pull_request".equalsIgnoreCase(eventType)) {
            log.info("Ignoring non-PR GitHub event: {}", eventType);
            return ResponseEntity.ok(Map.of(
                "status", "SKIPPED",
                "message", "Ignored event type: " + eventType
            ));
        }

        // 4. Parse JSON DTO
        GitHubWebhookDto payload;
        try {
            payload = objectMapper.readValue(rawPayload, GitHubWebhookDto.class);
        } catch (Exception e) {
            log.error("Failed to parse GitHub webhook JSON payload: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of(
                "status", "BAD_REQUEST",
                "message", "Invalid JSON payload: " + e.getMessage()
            ));
        }

        // 5. Process PR Event
        GitHubWebhookService.WebhookProcessingResult result =
            webhookService.processPullRequestWebhook(deliveryId, payload);

        return ResponseEntity.ok(result);
    }
}
