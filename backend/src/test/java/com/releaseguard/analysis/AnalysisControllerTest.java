package com.releaseguard.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.analysis.dto.AnalyzePullRequestRequest;
import com.releaseguard.ml.MlPredictionClient;
import com.releaseguard.ml.dto.MlPredictionResponse;
import com.releaseguard.entity.Project;
import com.releaseguard.entity.Source;
import com.releaseguard.repository.FindingRepository;
import com.releaseguard.repository.ProjectRepository;
import com.releaseguard.repository.SourceRepository;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.client.RestClient;

import java.util.Map;

@SpringBootTest(
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT
)
class AnalysisControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private SourceRepository sourceRepository;

    @Autowired
    private FindingRepository findingRepository;

    @MockitoBean
    private MlPredictionClient mlPredictionClient;

    private Long testProjectId;

    @BeforeEach
    void registerTestRepository() {

        String provider = "github";
        String owner = "StoryThreads";
        String repository = "releaseguard";

        Project project = new Project();

        project.setName(
            "Analysis Test " + System.nanoTime()
        );

        project.setDescription(
            "Integration test project"
        );

        project = projectRepository.save(project);

        Source source = new Source();

        source.setProject(project);
        source.setProvider(provider);
        source.setRepositoryOwner(owner);
        source.setRepositoryName(repository);
        source.setDefaultBranch("main");

        sourceRepository.save(source);

        testProjectId = project.getId();
    }

    @Test
    void shouldAnalyzePullRequestAndPersistFindings()
        throws Exception {

        MlPredictionResponse prediction =
            new MlPredictionResponse();

        prediction.setRiskLevel("MEDIUM");
        prediction.setRiskScore(50.0);

        prediction.setClassProbabilities(
            Map.of(
                "LOW", 0.10,
                "MEDIUM", 0.60,
                "HIGH", 0.25,
                "CRITICAL", 0.05
            )
        );

        prediction.setFeatureVector(
            Map.of(
                "changed_files", 1.0,
                "total_additions", 10.0,
                "total_deletions", 2.0
            )
        );

        prediction.setModelName(
            "xgboost_candidate"
        );

        prediction.setModelVersion(
            "1.0.0"
        );

        prediction.setFeatureVersion(
            "1.0.0"
        );

        prediction.setDatasetVersion(
            "1.0.0"
        );

        when(
            mlPredictionClient.predict(
                any(),
                any()
            )
        ).thenReturn(prediction);

        String owner =
            "StoryThreads";

        String repository =
            "releaseguard";

        long pullRequestNumber =
            1L;

        AnalyzePullRequestRequest request =
            new AnalyzePullRequestRequest();

        request.setProjectId(
            testProjectId
        );

        request.setOwner(
            owner
        );

        request.setRepository(
            repository
        );

        request.setPullRequestNumber(
            pullRequestNumber
        );

        RestClient client =
            RestClient.create();

        String response =
            client
                .post()
                .uri(
                    "http://localhost:{port}/api/analysis/pr",
                    port
                )
                .contentType(
                    MediaType.APPLICATION_JSON
                )
                .body(request)
                .retrieve()
                .body(String.class);

        assertNotNull(response);
        System.out.println(response);
        ObjectMapper objectMapper =
            new ObjectMapper();

        JsonNode root =
            objectMapper.readTree(response);

        JsonNode snapshot =
            root.get("snapshot");

        assertNotNull(snapshot);

        assertEquals(
            pullRequestNumber,
            snapshot
                .get("pullRequestNumber")
                .asLong()
        );

        assertEquals(
            owner,
            snapshot
                .get("owner")
                .asText()
        );

        assertEquals(
            repository,
            snapshot
                .get("repository")
                .asText()
        );

        assertNotNull(
            snapshot.get("title")
        );

        assertNotNull(
            snapshot.get("sourceBranch")
        );

        assertNotNull(
            snapshot.get("targetBranch")
        );

        assertNotNull(
            snapshot.get("headSha")
        );

        JsonNode changedFiles =
            snapshot.get("changedFiles");

        assertNotNull(changedFiles);

        assertFalse(
            changedFiles.isEmpty()
        );

        JsonNode changeId =
            root.get("changeId");

        assertNotNull(changeId);

        assertTrue(
            changeId.asLong() > 0
        );

        JsonNode findings =
            root.get("findings");

        assertNotNull(findings);

        assertEquals(
            findings.size(),
            findingRepository.countByChangeId(
                changeId.asLong()
            )
        );

        JsonNode riskAnalysis =
            root.get("riskAnalysis");

        assertNotNull(riskAnalysis);

        assertEquals(
            "MEDIUM",
            riskAnalysis
                .get("riskLevel")
                .asText()
        );

        assertEquals(
            50.0,
            riskAnalysis
                .get("riskScore")
                .asDouble()
        );

        assertEquals(
            "xgboost_candidate",
            riskAnalysis
                .get("modelName")
                .asText()
        );

        assertEquals(
            "1.0.0",
            riskAnalysis
                .get("modelVersion")
                .asText()
        );

        assertEquals(
            "1.0.0",
            riskAnalysis
                .get("featureVersion")
                .asText()
        );

        assertEquals(
            "1.0.0",
            riskAnalysis
                .get("datasetVersion")
                .asText()
        );
    }
}
