package com.releaseguard.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.analysis.dto.AnalyzePullRequestRequest;
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

    @Test
    void shouldAnalyzePullRequest() throws Exception {

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

        JsonNode root =
            objectMapper.readTree(response);

        JsonNode snapshot =
            root.get("snapshot");

        assertNotNull(snapshot);

        assertEquals(
            pullRequestNumber,
            snapshot.get("pullRequestNumber").asLong()
        );

        assertEquals(
            owner,
            snapshot.get("owner").asText()
        );

        assertEquals(
            repository,
            snapshot.get("repository").asText()
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
        assertFalse(changedFiles.isEmpty());
    }
}
