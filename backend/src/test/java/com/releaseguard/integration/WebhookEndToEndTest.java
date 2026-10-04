package com.releaseguard.integration;

import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.entity.*;
import com.releaseguard.ml.dto.MlPredictionResponse;
import com.releaseguard.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.*;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class WebhookEndToEndTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private SourceRepository sourceRepository;

    @Autowired
    private ChangeRepository changeRepository;

    @Autowired
    private FindingRepository findingRepository;

    @Autowired
    private MlPredictionRepository mlPredictionRepository;

    @Autowired
    private ProcessedEventRepository processedEventRepository;

    @MockitoBean
    private AnalysisService analysisService;

    private static final String WEBHOOK_SECRET = "releaseguard-webhook-secret-dev";

    @BeforeEach
    void setup() {
        findingRepository.deleteAll();
        mlPredictionRepository.deleteAll();
        changeRepository.deleteAll();
        sourceRepository.deleteAll();
        projectRepository.deleteAll();
        processedEventRepository.deleteAll();
    }

    private String calculateSignature(byte[] payload) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(WEBHOOK_SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] hash = mac.doFinal(payload);
        StringBuilder sb = new StringBuilder("sha256=");
        for (byte b : hash) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    @Test
    @DisplayName("V0.9.6 / V0.9.7: Webhook Ingestion & Automated PR Analysis Pipeline")
    void testWebhookIngestionAndAutomaticAnalysis() throws Exception {
        // Arrange mock analysis response
        ChangeSnapshot mockSnapshot = new ChangeSnapshot();
        mockSnapshot.setOwner("facebook");
        mockSnapshot.setRepository("react");
        mockSnapshot.setPullRequestNumber(123L);
        mockSnapshot.setTitle("Optimize reconciler hooks");

        MlPredictionResponse mockPrediction = new MlPredictionResponse();
        mockPrediction.setRiskLevel("HIGH");
        mockPrediction.setRiskScore(0.82);
        mockPrediction.setClassProbabilities(Map.of("LOW", 0.05, "MEDIUM", 0.13, "HIGH", 0.82, "CRITICAL", 0.00));
        mockPrediction.setFeatureVector(Map.of("total_files_changed", 14.0));
        mockPrediction.setModelName("xgboost");
        mockPrediction.setModelVersion("2.0.0");
        mockPrediction.setFeatureVersion("1.0.0");
        mockPrediction.setDatasetVersion("2.0.0");

        when(analysisService.analyzePullRequest(any(), anyString(), anyString(), anyLong()))
            .thenAnswer(inv -> {
                Long projectId = inv.getArgument(0);
                long prNumber = inv.getArgument(3);

                Source s = sourceRepository.findByProjectId(projectId).get(0);

                Change c = new Change();
                c.setSource(s);
                c.setExternalChangeId(String.valueOf(prNumber));
                c.setTitle("Optimize reconciler hooks");
                c.setAuthor("danabramov");
                c.setBaseRevision("main");
                c.setHeadRevision("feat/opt");
                c.setStatus("OPEN");
                c = changeRepository.save(c);

                FindingEntity finding = new FindingEntity();
                finding.setChange(c);
                finding.setAnalyzerType("SECURITY");
                finding.setFindingType("INJECTION");
                finding.setSeverity("HIGH");
                finding.setRuleId("SEC-001");
                finding.setTitle("Potential memory leak");
                finding.setMessage("Hook closure retains detached DOM node");
                finding.setFilePath("packages/react-reconciler/src/ReactFiberHooks.js");
                finding.setLineNumber(452);
                findingRepository.save(finding);

                MlPredictionEntity predEntity = new MlPredictionEntity();
                predEntity.setChange(c);
                predEntity.setRiskLevel(mockPrediction.getRiskLevel());
                predEntity.setRiskScore(mockPrediction.getRiskScore());
                predEntity.setClassProbabilities("{\"LOW\":0.05,\"MEDIUM\":0.13,\"HIGH\":0.82,\"CRITICAL\":0.00}");
                predEntity.setFeatureVector("{\"total_files_changed\":14}");
                predEntity.setModelName(mockPrediction.getModelName());
                predEntity.setModelVersion(mockPrediction.getModelVersion());
                predEntity.setFeatureVersion(mockPrediction.getFeatureVersion());
                predEntity.setDatasetVersion(mockPrediction.getDatasetVersion());
                mlPredictionRepository.save(predEntity);

                return new AnalyzePullRequestResponse(
                    mockSnapshot,
                    c.getId(),
                    Collections.emptyList(),
                    mockPrediction
                );
            });

        String payloadJson = """
            {
              "action": "opened",
              "number": 123,
              "pull_request": {
                "number": 123,
                "title": "Optimize reconciler hooks",
                "state": "open",
                "user": {"login": "danabramov"},
                "head": {"sha": "abc1234", "ref": "feat/opt"},
                "base": {"sha": "def5678", "ref": "main"}
              },
              "repository": {
                "name": "react",
                "full_name": "facebook/react",
                "owner": {"login": "facebook"}
              }
            }
            """;

        byte[] payloadBytes = payloadJson.getBytes(StandardCharsets.UTF_8);
        String signature = calculateSignature(payloadBytes);
        String deliveryId = "deliv-" + UUID.randomUUID();

        // 1. Post valid webhook
        mockMvc.perform(post("/api/webhooks/github")
                .header("X-GitHub-Event", "pull_request")
                .header("X-GitHub-Delivery", deliveryId)
                .header("X-Hub-Signature-256", signature)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payloadBytes))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status", is("COMPLETED")))
            .andExpect(jsonPath("$.deliveryId", is(deliveryId)))
            .andExpect(jsonPath("$.changeId", notNullValue()));

        // 2. Test duplicate webhook protection
        mockMvc.perform(post("/api/webhooks/github")
                .header("X-GitHub-Event", "pull_request")
                .header("X-GitHub-Delivery", deliveryId)
                .header("X-Hub-Signature-256", signature)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payloadBytes))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status", is("DUPLICATE_IGNORED")));

        // 3. Test invalid signature rejection (401 Unauthorized)
        mockMvc.perform(post("/api/webhooks/github")
                .header("X-GitHub-Event", "pull_request")
                .header("X-GitHub-Delivery", "another-" + UUID.randomUUID())
                .header("X-Hub-Signature-256", "sha256=invalidhash1234567890abcdef")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payloadBytes))
            .andExpect(status().isUnauthorized());

        // 4. Verify propagation to Dashboard API (GET /api/changes/recent)
        mockMvc.perform(get("/api/changes/recent"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(1)))
            .andExpect(jsonPath("$[0].change.externalChangeId", is("123")))
            .andExpect(jsonPath("$[0].prediction.riskLevel", is("HIGH")))
            .andExpect(jsonPath("$[0].findings", hasSize(1)))
            .andExpect(jsonPath("$[0].findings[0].ruleId", is("SEC-001")));

        // 5. Verify Project Summary API (GET /api/projects/{id}/summary)
        Project project = projectRepository.findAll().get(0);
        mockMvc.perform(get("/api/projects/{id}/summary", project.getId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.project.name", is("facebook/react")))
            .andExpect(jsonPath("$.changesCount", is(1)))
            .andExpect(jsonPath("$.riskCounts.HIGH", is(1)))
            .andExpect(jsonPath("$.averageRiskScore", is(0.82)));
    }
}
