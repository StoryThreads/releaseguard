package com.releaseguard.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.analysis.dto.AnalyzePullRequestRequest;
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
import org.springframework.web.client.RestClient;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class AnalysisControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private SourceRepository sourceRepository;

    @Autowired
    private FindingRepository findingRepository;

    @BeforeEach
    void registerTestRepository() {

        String owner = "StoryThreads";
        String repository = "releaseguard";

        Project project = new Project();
        project.setName("Analysis Test " + System.nanoTime());
        project.setDescription("Integration test project");
        project = projectRepository.save(project);

        Source source = new Source();
        source.setProject(project);
        source.setProvider("github");
        source.setRepositoryOwner(owner);
        source.setRepositoryName(repository);
        source.setDefaultBranch("main");

        sourceRepository.save(source);
    }

    @Test
    void shouldAnalyzePullRequestAndPersistFindings() throws Exception {

        String owner = "StoryThreads";
        String repository = "releaseguard";
        long pullRequestNumber = 1;

        AnalyzePullRequestRequest request =
            new AnalyzePullRequestRequest();

        request.setOwner(owner);
        request.setRepository(repository);
        request.setPullRequestNumber(pullRequestNumber);

        RestClient client = RestClient.create();

        String response = client
            .post()
            .uri(
                "http://localhost:{port}/api/analysis/pr",
                port
            )
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(String.class);

        assertNotNull(response);

        ObjectMapper objectMapper = new ObjectMapper();
        JsonNode root = objectMapper.readTree(response);
        JsonNode snapshot = root.get("snapshot");

        assertNotNull(snapshot);
        assertEquals(
            pullRequestNumber,
            snapshot.get("pullRequestNumber").asLong()
        );
        assertEquals(owner, snapshot.get("owner").asText());
        assertEquals(repository, snapshot.get("repository").asText());
        assertNotNull(snapshot.get("title"));
        assertNotNull(snapshot.get("sourceBranch"));
        assertNotNull(snapshot.get("targetBranch"));
        assertNotNull(snapshot.get("headSha"));

        JsonNode changedFiles = snapshot.get("changedFiles");
        assertNotNull(changedFiles);
        assertFalse(changedFiles.isEmpty());

        JsonNode changeId = root.get("changeId");
        JsonNode findings = root.get("findings");

        assertNotNull(changeId);
        assertTrue(changeId.asLong() > 0);
        assertNotNull(findings);

        assertEquals(
            findings.size(),
            findingRepository.countByChangeId(changeId.asLong())
        );
    }
}
