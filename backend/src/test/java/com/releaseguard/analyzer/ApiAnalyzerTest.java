package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApiAnalyzerTest {

    private final ApiAnalyzer analyzer = new ApiAnalyzer();

    @Test
    void shouldDetectGetMappingChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("UserController.java");
        file.setStatus("modified");
        file.setPatch("""
                @@ -10,5 +10,6 @@
                 @RestController
                 public class UserController {
                +    @GetMapping("/users")
                     public List<User> getUsers() {
                         return service.findAll();
                     }
                 }
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("API-001", findings.get(0).ruleId());
        assertEquals(AnalyzerType.API, findings.get(0).analyzerType());
        assertEquals("UserController.java", findings.get(0).filePath());
    }

    @Test
    void shouldDetectPostMappingChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("UserController.java");
        file.setStatus("modified");
        file.setPatch("""
                @@ -15,5 +15,6 @@
                 public class UserController {
                +    @PostMapping("/users")
                     public User createUser() {
                         return service.create();
                     }
                 }
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("API-001", findings.get(0).ruleId());
    }

    @Test
    void shouldDetectDeleteMappingChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("UserController.java");
        file.setStatus("modified");
        file.setPatch("""
                @@ -20,5 +20,6 @@
                 public class UserController {
                +    @DeleteMapping("/users/{id}")
                     public void deleteUser(Long id) {
                         service.delete(id);
                     }
                 }
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
    }

    @Test
    void shouldIgnoreNonJavaFile() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("README.md");
        file.setStatus("modified");
        file.setPatch("""
                @@ -1,2 +1,3 @@
                +@GetMapping("/users")
                 Documentation
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreUnrelatedJavaChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("UserService.java");
        file.setStatus("modified");
        file.setPatch("""
                @@ -10,4 +10,5 @@
                 public class UserService {
                +    private String name;
                 }
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreDiffMetadataLines() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("UserController.java");
        file.setStatus("modified");
        file.setPatch("""
                --- a/UserController.java
                +++ b/UserController.java
                @@ -1,3 +1,3 @@
                 public class UserController {
                 }
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldReturnEmptyWhenContextIsNull() {

        List<Finding> findings = analyzer.analyze(null);

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldReturnEmptyWhenSnapshotIsNull() {

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(null)
        );

        assertTrue(findings.isEmpty());
    }
}
