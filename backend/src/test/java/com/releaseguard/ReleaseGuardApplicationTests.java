package com.releaseguard;

import com.releaseguard.repository.ChangeRepository;
import com.releaseguard.repository.ProjectRepository;
import com.releaseguard.repository.SourceRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ReleaseGuardApplicationTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ChangeRepository changeRepository;

    @Autowired
    private SourceRepository sourceRepository;

    @Autowired
    private ProjectRepository projectRepository;

    @BeforeEach
    void cleanDatabase() {
        /*
         * Delete child records first because of foreign-key constraints:
         *
         * changes -> sources -> projects
         */
        changeRepository.deleteAllInBatch();
        sourceRepository.deleteAllInBatch();
        projectRepository.deleteAllInBatch();
    }

    // ============================================================
    // PROJECT TESTS
    // ============================================================

    @Test
    void shouldCreateProject() throws Exception {

        String request = """
            {
                "name": "ReleaseGuard",
                "description": "AI-powered release analysis platform"
            }
            """;

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id", notNullValue()))
            .andExpect(jsonPath("$.name", is("ReleaseGuard")))
            .andExpect(
                jsonPath(
                    "$.description",
                    is("AI-powered release analysis platform")
                )
            )
            .andExpect(jsonPath("$.createdAt", notNullValue()))
            .andExpect(jsonPath("$.updatedAt", notNullValue()));
    }

    @Test
    void shouldGetProjectById() throws Exception {

        String createRequest = """
            {
                "name": "ReleaseGuard",
                "description": "Release analysis platform"
            }
            """;

        String response = mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(createRequest)
            )
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        long projectId = extractId(response);

        mockMvc.perform(
                get("/api/projects/" + projectId)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id", is((int) projectId)))
            .andExpect(jsonPath("$.name", is("ReleaseGuard")))
            .andExpect(
                jsonPath(
                    "$.description",
                    is("Release analysis platform")
                )
            );
    }

    @Test
    void shouldGetAllProjects() throws Exception {

        String firstProject = """
            {
                "name": "Project One",
                "description": "First project"
            }
            """;

        String secondProject = """
            {
                "name": "Project Two",
                "description": "Second project"
            }
            """;

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(firstProject)
            )
            .andExpect(status().isCreated());

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(secondProject)
            )
            .andExpect(status().isCreated());

        mockMvc.perform(
                get("/api/projects")
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void shouldRejectInvalidProject() throws Exception {

        String request = """
            {
                "name": "",
                "description": "Invalid project"
            }
            """;

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status", is(400)))
            .andExpect(jsonPath("$.error", is("VALIDATION_ERROR")))
            .andExpect(
                jsonPath(
                    "$.message",
                    is("Request validation failed")
                )
            )
            .andExpect(jsonPath("$.details.name", notNullValue()));
    }

    @Test
    void shouldReturnNotFoundForMissingProject() throws Exception {

        mockMvc.perform(
                get("/api/projects/999999")
            )
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status", is(404)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("RESOURCE_NOT_FOUND")
                )
            );
    }

    @Test
    void shouldRejectDuplicateProject() throws Exception {

        String request = """
            {
                "name": "DuplicateProject",
                "description": "Test project"
            }
            """;

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated());

        mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.status", is(409)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("CONFLICT")
                )
            );
    }

    // ============================================================
    // SOURCE TESTS
    // ============================================================

    @Test
    void shouldCreateSource() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        String request = """
            {
                "projectId": %d,
                "provider": "GITHUB",
                "repositoryOwner": "releaseguard",
                "repositoryName": "releaseguard",
                "defaultBranch": "main"
            }
            """.formatted(projectId);

        mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id", notNullValue()))
            .andExpect(jsonPath("$.projectId", is((int) projectId)))
            .andExpect(jsonPath("$.provider", is("GITHUB")))
            .andExpect(
                jsonPath(
                    "$.repositoryOwner",
                    is("releaseguard")
                )
            )
            .andExpect(
                jsonPath(
                    "$.repositoryName",
                    is("releaseguard")
                )
            )
            .andExpect(
                jsonPath(
                    "$.defaultBranch",
                    is("main")
                )
            )
            .andExpect(jsonPath("$.createdAt", notNullValue()))
            .andExpect(jsonPath("$.updatedAt", notNullValue()));
    }

    @Test
    void shouldGetSourceById() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        long sourceId = createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "releaseguard",
            "main"
        );

        mockMvc.perform(
                get("/api/sources/" + sourceId)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id", is((int) sourceId)))
            .andExpect(jsonPath("$.projectId", is((int) projectId)))
            .andExpect(jsonPath("$.provider", is("GITHUB")))
            .andExpect(
                jsonPath(
                    "$.repositoryOwner",
                    is("releaseguard")
                )
            )
            .andExpect(
                jsonPath(
                    "$.repositoryName",
                    is("releaseguard")
                )
            );
    }

    @Test
    void shouldGetSourcesByProject() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "repository-one",
            "main"
        );

        createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "repository-two",
            "main"
        );

        mockMvc.perform(
                get("/api/sources/project/" + projectId)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void shouldRejectInvalidSource() throws Exception {

        String request = """
            {
                "projectId": null,
                "provider": "",
                "repositoryOwner": "",
                "repositoryName": "",
                "defaultBranch": ""
            }
            """;

        mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status", is(400)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("VALIDATION_ERROR")
                )
            )
            .andExpect(jsonPath("$.details", notNullValue()));
    }

    @Test
    void shouldReturnNotFoundForMissingSource() throws Exception {

        mockMvc.perform(
                get("/api/sources/999999")
            )
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status", is(404)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("RESOURCE_NOT_FOUND")
                )
            );
    }

    @Test
    void shouldRejectSourceForMissingProject() throws Exception {

        String request = """
            {
                "projectId": 999999,
                "provider": "GITHUB",
                "repositoryOwner": "releaseguard",
                "repositoryName": "releaseguard",
                "defaultBranch": "main"
            }
            """;

        mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isNotFound())
            .andExpect(
                jsonPath(
                    "$.error",
                    is("RESOURCE_NOT_FOUND")
                )
            );
    }

    @Test
    void shouldRejectDuplicateSource() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        String request = """
            {
                "projectId": %d,
                "provider": "GITHUB",
                "repositoryOwner": "releaseguard",
                "repositoryName": "releaseguard",
                "defaultBranch": "main"
            }
            """.formatted(projectId);

        mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated());

        mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.status", is(409)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("CONFLICT")
                )
            );
    }

    // ============================================================
    // CHANGE TESTS
    // ============================================================

    @Test
    void shouldCreateChange() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        long sourceId = createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "releaseguard",
            "main"
        );

        String request = """
            {
                "sourceId": %d,
                "externalChangeId": "PR-101",
                "title": "Improve release analysis",
                "author": "Vedant",
                "baseRevision": "abc123",
                "headRevision": "def456",
                "status": "OPEN"
            }
            """.formatted(sourceId);

        mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id", notNullValue()))
            .andExpect(jsonPath("$.sourceId", is((int) sourceId)))
            .andExpect(
                jsonPath(
                    "$.externalChangeId",
                    is("PR-101")
                )
            )
            .andExpect(
                jsonPath(
                    "$.title",
                    is("Improve release analysis")
                )
            )
            .andExpect(
                jsonPath(
                    "$.author",
                    is("Vedant")
                )
            )
            .andExpect(
                jsonPath(
                    "$.baseRevision",
                    is("abc123")
                )
            )
            .andExpect(
                jsonPath(
                    "$.headRevision",
                    is("def456")
                )
            )
            .andExpect(
                jsonPath(
                    "$.status",
                    is("OPEN")
                )
            )
            .andExpect(jsonPath("$.createdAt", notNullValue()))
            .andExpect(jsonPath("$.updatedAt", notNullValue()));
    }

    @Test
    void shouldGetChangeById() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        long sourceId = createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "releaseguard",
            "main"
        );

        long changeId = createChange(
            sourceId,
            "PR-101",
            "Improve release analysis",
            "Vedant",
            "abc123",
            "def456",
            "OPEN"
        );

        mockMvc.perform(
                get("/api/changes/" + changeId)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id", is((int) changeId)))
            .andExpect(jsonPath("$.sourceId", is((int) sourceId)))
            .andExpect(
                jsonPath(
                    "$.externalChangeId",
                    is("PR-101")
                )
            )
            .andExpect(
                jsonPath(
                    "$.title",
                    is("Improve release analysis")
                )
            )
            .andExpect(
                jsonPath(
                    "$.status",
                    is("OPEN")
                )
            );
    }

    @Test
    void shouldGetChangesBySource() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        long sourceId = createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "releaseguard",
            "main"
        );

        createChange(
            sourceId,
            "PR-101",
            "First change",
            "Author One",
            "abc123",
            "def456",
            "OPEN"
        );

        createChange(
            sourceId,
            "PR-102",
            "Second change",
            "Author Two",
            "def456",
            "ghi789",
            "MERGED"
        );

        mockMvc.perform(
                get("/api/changes/source/" + sourceId)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void shouldRejectInvalidChange() throws Exception {

        String request = """
            {
                "sourceId": null,
                "externalChangeId": "",
                "title": "",
                "author": "",
                "baseRevision": "",
                "headRevision": "",
                "status": ""
            }
            """;

        mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status", is(400)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("VALIDATION_ERROR")
                )
            )
            .andExpect(jsonPath("$.details", notNullValue()));
    }

    @Test
    void shouldReturnNotFoundForMissingChange() throws Exception {

        mockMvc.perform(
                get("/api/changes/999999")
            )
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status", is(404)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("RESOURCE_NOT_FOUND")
                )
            );
    }

    @Test
    void shouldRejectChangeForMissingSource() throws Exception {

        String request = """
            {
                "sourceId": 999999,
                "externalChangeId": "PR-999",
                "title": "Invalid change",
                "author": "Test Author",
                "baseRevision": "abc123",
                "headRevision": "def456",
                "status": "OPEN"
            }
            """;

        mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isNotFound())
            .andExpect(
                jsonPath(
                    "$.error",
                    is("RESOURCE_NOT_FOUND")
                )
            );
    }

    @Test
    void shouldRejectDuplicateChange() throws Exception {

        long projectId = createProject(
            "ReleaseGuard",
            "ReleaseGuard project"
        );

        long sourceId = createSource(
            projectId,
            "GITHUB",
            "releaseguard",
            "releaseguard",
            "main"
        );

        String request = """
            {
                "sourceId": %d,
                "externalChangeId": "PR-101",
                "title": "Improve release analysis",
                "author": "Vedant",
                "baseRevision": "abc123",
                "headRevision": "def456",
                "status": "OPEN"
            }
            """.formatted(sourceId);

        mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated());

        mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.status", is(409)))
            .andExpect(
                jsonPath(
                    "$.error",
                    is("CONFLICT")
                )
            );
    }

    // ============================================================
    // HELPER METHODS
    // ============================================================

    private long createProject(
        String name,
        String description
    ) throws Exception {

        String request = """
            {
                "name": "%s",
                "description": "%s"
            }
            """.formatted(name, description);

        String response = mockMvc.perform(
                post("/api/projects")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        return extractId(response);
    }

    private long createSource(
        long projectId,
        String provider,
        String owner,
        String repository,
        String branch
    ) throws Exception {

        String request = """
            {
                "projectId": %d,
                "provider": "%s",
                "repositoryOwner": "%s",
                "repositoryName": "%s",
                "defaultBranch": "%s"
            }
            """.formatted(
            projectId,
            provider,
            owner,
            repository,
            branch
        );

        String response = mockMvc.perform(
                post("/api/sources")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        return extractId(response);
    }

    private long createChange(
        long sourceId,
        String externalChangeId,
        String title,
        String author,
        String baseRevision,
        String headRevision,
        String status
    ) throws Exception {

        String request = """
            {
                "sourceId": %d,
                "externalChangeId": "%s",
                "title": "%s",
                "author": "%s",
                "baseRevision": "%s",
                "headRevision": "%s",
                "status": "%s"
            }
            """.formatted(
            sourceId,
            externalChangeId,
            title,
            author,
            baseRevision,
            headRevision,
            status
        );

        String response = mockMvc.perform(
                post("/api/changes")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request)
            )
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        return extractId(response);
    }

    private long extractId(String json) {

        String idValue = json
            .replaceAll(
                ".*\"id\"\\s*:\\s*(\\d+).*",
                "$1"
            );

        return Long.parseLong(idValue);
    }
}
