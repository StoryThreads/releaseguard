package com.releaseguard.ml;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.analysis.AnalysisService;
import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.entity.Change;
import com.releaseguard.entity.MlPredictionEntity;
import com.releaseguard.entity.Project;
import com.releaseguard.entity.Source;
import com.releaseguard.github.GitHubRestAdapter;
import com.releaseguard.github.dto.GitHubPullRequestFileResponse;
import com.releaseguard.github.dto.GitHubPullRequestResponse;
import com.releaseguard.repository.ChangeRepository;
import com.releaseguard.repository.FindingRepository;
import com.releaseguard.repository.MlPredictionRepository;
import com.releaseguard.repository.ProjectRepository;
import com.releaseguard.repository.SourceRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@SpringBootTest
class MlPredictionEndToEndTest {

    private static final String OWNER = "releaseguard";
    private static final String REPOSITORY = "ml-e2e-test";
    private static final long PULL_REQUEST_NUMBER = 101L;

    @Autowired
    private AnalysisService analysisService;

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
    private ObjectMapper objectMapper;

    @Autowired
    private PlatformTransactionManager transactionManager;

    /*
     * GitHub is the external dependency that we do not want
     * this E2E test to contact.
     *
     * Everything after AnalysisService remains real:
     *
     * AnalysisService
     *      ↓
     * AnalyzerEngine
     *      ↓
     * MlPredictionClient
     *      ↓
     * FastAPI
     *      ↓
     * XGBoost
     *      ↓
     * Persistence
     */
    @MockitoBean
    private GitHubRestAdapter githubRestAdapter;

    private Long projectId;
    private Long sourceId;

    @BeforeEach
    void setUp() {

        Project project = new Project();

        project.setName(
            "ReleaseGuard ML E2E " + UUID.randomUUID()
        );

        project.setDescription(
            "V0.5.7 end-to-end ML pipeline test"
        );

        project =
            projectRepository.save(project);

        projectId =
            project.getId();

        Source source = new Source();

        source.setProject(project);
        source.setProvider("GITHUB");
        source.setRepositoryOwner(OWNER);
        source.setRepositoryName(REPOSITORY);
        source.setDefaultBranch("main");

        source =
            sourceRepository.save(source);

        sourceId =
            source.getId();

        when(
            githubRestAdapter.getPullRequest(
                eq(OWNER),
                eq(REPOSITORY),
                eq(PULL_REQUEST_NUMBER)
            )
        ).thenReturn(
            createPullRequest()
        );

        when(
            githubRestAdapter.getPullRequestFiles(
                eq(OWNER),
                eq(REPOSITORY),
                eq(PULL_REQUEST_NUMBER)
            )
        ).thenReturn(
            List.of(createChangedFile())
        );
    }

    @AfterEach
    void cleanUp() {

        if (sourceId == null && projectId == null) {
            return;
        }

        TransactionTemplate transactionTemplate =
            new TransactionTemplate(transactionManager);

        transactionTemplate.executeWithoutResult(status -> {

            if (sourceId != null) {

                List<Change> changes =
                    changeRepository.findBySourceId(sourceId);

                for (Change change : changes) {

                    Long changeId = change.getId();

                    if (changeId == null) {
                        continue;
                    }

                    mlPredictionRepository
                        .findByChangeId(changeId)
                        .ifPresent(prediction ->
                            mlPredictionRepository.deleteById(
                                prediction.getId()
                            )
                        );

                    findingRepository.deleteByChangeId(
                        changeId
                    );

                    changeRepository.deleteById(
                        changeId
                    );
                }

                sourceRepository.deleteById(
                    sourceId
                );
            }

            if (projectId != null) {

                projectRepository.deleteById(
                    projectId
                );
            }
        });

        sourceId = null;
        projectId = null;
    }

    @Test
    void shouldRunCompleteMlPipelineAndPersistPrediction()
        throws Exception {

        /*
         * This is the actual cross-service execution.
         *
         * MlPredictionClient is NOT mocked.
         *
         * Therefore this call must reach:
         *
         * http://localhost:8000/api/v1/predict
         */
        AnalyzePullRequestResponse response =
            analysisService.analyzePullRequest(
                projectId,
                OWNER,
                REPOSITORY,
                PULL_REQUEST_NUMBER
            );

        /*
         * --------------------------------------------------------
         * 1. Verify Spring Boot analysis completed
         * --------------------------------------------------------
         */

        assertNotNull(response);

        assertNotNull(
            response.getSnapshot()
        );

        assertNotNull(
            response.getChangeId()
        );

        assertNotNull(
            response.getFindings()
        );

        assertNotNull(
            response.getRiskAnalysis()
        );

        /*
         * --------------------------------------------------------
         * 2. Verify ChangeSnapshot reached ML pipeline
         * --------------------------------------------------------
         */

        assertEquals(
            PULL_REQUEST_NUMBER,
            response
                .getSnapshot()
                .getPullRequestNumber()
        );

        assertEquals(
            OWNER,
            response
                .getSnapshot()
                .getOwner()
        );

        assertEquals(
            REPOSITORY,
            response
                .getSnapshot()
                .getRepository()
        );

        /*
         * --------------------------------------------------------
         * 3. Verify model metadata returned by FastAPI
         * --------------------------------------------------------
         */

        assertEquals(
            "xgboost",
            response
                .getRiskAnalysis()
                .getModelName()
        );

        assertEquals(
            "2.0.0",
            response
                .getRiskAnalysis()
                .getModelVersion()
        );

        assertEquals(
            "1.0.0",
            response
                .getRiskAnalysis()
                .getFeatureVersion()
        );

        assertEquals(
            "2.0.0",
            response
                .getRiskAnalysis()
                .getDatasetVersion()
        );

        /*
         * --------------------------------------------------------
         * 4. Verify risk level
         * --------------------------------------------------------
         */

        assertTrue(
            List.of(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL"
            ).contains(
                response
                    .getRiskAnalysis()
                    .getRiskLevel()
            )
        );

        /*
         * --------------------------------------------------------
         * 5. Verify numerical risk score
         * --------------------------------------------------------
         */

        assertTrue(
            response
                .getRiskAnalysis()
                .getRiskScore() >= 0.0
                &&
                response
                    .getRiskAnalysis()
                    .getRiskScore() <= 100.0
        );

        /*
         * --------------------------------------------------------
         * 6. Verify class probabilities
         * --------------------------------------------------------
         */

        Map<String, Double> probabilities =
            response
                .getRiskAnalysis()
                .getClassProbabilities();

        assertNotNull(probabilities);

        assertEquals(
            4,
            probabilities.size()
        );

        assertTrue(
            probabilities.keySet().containsAll(
                List.of(
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL"
                )
            )
        );

        assertEquals(
            1.0,
            probabilities.values()
                .stream()
                .mapToDouble(v -> v != null ? v : 0.0)
                .sum(),
            1.0e-6
        );

        /*
         * --------------------------------------------------------
         * 7. Verify feature vector returned by Python
         * --------------------------------------------------------
         */

        Map<String, Double> returnedFeatureVector =
            response
                .getRiskAnalysis()
                .getFeatureVector();

        assertNotNull(
            returnedFeatureVector
        );

        assertEquals(
            28,
            returnedFeatureVector.size()
        );

        /*
         * --------------------------------------------------------
         * 8. Verify Change was persisted
         * --------------------------------------------------------
         */

        Change change =
            changeRepository
                .findById(
                    response.getChangeId()
                )
                .orElseThrow();

        assertEquals(
            sourceId,
            change
                .getSource()
                .getId()
        );

        /*
         * --------------------------------------------------------
         * 9. Verify ML prediction was persisted
         * --------------------------------------------------------
         */

        MlPredictionEntity persistedPrediction =
            mlPredictionRepository
                .findByChangeId(
                    change.getId()
                )
                .orElseThrow();

        assertEquals(
            change.getId(),
            persistedPrediction
                .getChange()
                .getId()
        );

        assertEquals(
            response
                .getRiskAnalysis()
                .getRiskLevel(),
            persistedPrediction
                .getRiskLevel()
        );

        assertEquals(
            response
                .getRiskAnalysis()
                .getRiskScore(),
            persistedPrediction
                .getRiskScore(),
            1.0e-9
        );

        assertEquals(
            "xgboost",
            persistedPrediction
                .getModelName()
        );

        assertEquals(
            "2.0.0",
            persistedPrediction
                .getModelVersion()
        );

        assertEquals(
            "1.0.0",
            persistedPrediction
                .getFeatureVersion()
        );

        assertEquals(
            "2.0.0",
            persistedPrediction
                .getDatasetVersion()
        );

        /*
         * --------------------------------------------------------
         * 10. Verify persisted probabilities
         * --------------------------------------------------------
         */

        Map<String, Double> persistedProbabilities =
            objectMapper.readValue(
                persistedPrediction
                    .getClassProbabilities(),
                new TypeReference<Map<String, Double>>() {}
            );

        assertEquals(
            probabilities,
            persistedProbabilities
        );

        /*
         * --------------------------------------------------------
         * 11. Verify persisted feature vector
         * --------------------------------------------------------
         */

        Map<String, Double> persistedFeatureVector =
            objectMapper.readValue(
                persistedPrediction
                    .getFeatureVector(),
                new TypeReference<Map<String, Double>>() {}
            );

        assertEquals(
            returnedFeatureVector,
            persistedFeatureVector
        );
    }

    private GitHubPullRequestResponse createPullRequest() {

        GitHubPullRequestResponse pullRequest =
            new GitHubPullRequestResponse();

        pullRequest.setNumber(
            PULL_REQUEST_NUMBER
        );

        pullRequest.setTitle(
            "ML pipeline integration test"
        );

        pullRequest.setState(
            "open"
        );

        GitHubPullRequestResponse.User user =
            new GitHubPullRequestResponse.User();

        user.setLogin(
            "releaseguard-test"
        );

        pullRequest.setUser(
            user
        );

        GitHubPullRequestResponse.Branch base =
            new GitHubPullRequestResponse.Branch();

        base.setRef(
            "main"
        );

        base.setSha(
            "base-sha-101"
        );

        pullRequest.setBase(
            base
        );

        GitHubPullRequestResponse.Branch head =
            new GitHubPullRequestResponse.Branch();

        head.setRef(
            "feature/ml-e2e"
        );

        head.setSha(
            "head-sha-101"
        );

        pullRequest.setHead(
            head
        );

        return pullRequest;
    }

    private GitHubPullRequestFileResponse createChangedFile() {

        GitHubPullRequestFileResponse file =
            new GitHubPullRequestFileResponse();

        file.setFilename(
            "src/main/java/com/releaseguard/E2eController.java"
        );

        file.setStatus(
            "modified"
        );

        file.setAdditions(
            20
        );

        file.setDeletions(
            5
        );

        file.setChanges(
            25
        );

        file.setPatch("""
            @@ -10,6 +10,21 @@
            +public void update() {
            +    System.out.println("debug");
            +}
            """);

        return file;
    }
}
