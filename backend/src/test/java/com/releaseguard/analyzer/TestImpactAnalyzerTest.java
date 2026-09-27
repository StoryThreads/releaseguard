package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TestImpactAnalyzerTest {

    private final TestImpactAnalyzer analyzer =
        new TestImpactAnalyzer();

    @Test
    void shouldDetectProductionChangeWithoutTestChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile productionFile =
            new ChangeSnapshot.ChangedFile();

        productionFile.setFilename(
            "src/main/java/com/releaseguard/service/UserService.java"
        );
        productionFile.setStatus("modified");

        snapshot.setChangedFiles(List.of(productionFile));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());

        assertEquals(
            "TEST-001",
            findings.get(0).ruleId()
        );

        assertEquals(
            AnalyzerType.TEST_IMPACT,
            findings.get(0).analyzerType()
        );

        assertEquals(
            "src/main/java/com/releaseguard/service/UserService.java",
            findings.get(0).filePath()
        );
    }

    @Test
    void shouldNotReportWhenCorrespondingTestAlsoChanges() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile productionFile =
            new ChangeSnapshot.ChangedFile();

        productionFile.setFilename(
            "src/main/java/com/releaseguard/service/UserService.java"
        );
        productionFile.setStatus("modified");

        ChangeSnapshot.ChangedFile testFile =
            new ChangeSnapshot.ChangedFile();

        testFile.setFilename(
            "src/test/java/com/releaseguard/service/UserServiceTest.java"
        );
        testFile.setStatus("modified");

        snapshot.setChangedFiles(
            List.of(
                productionFile,
                testFile
            )
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreTestFiles() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile testFile =
            new ChangeSnapshot.ChangedFile();

        testFile.setFilename(
            "src/test/java/com/releaseguard/service/UserServiceTest.java"
        );
        testFile.setStatus("modified");

        snapshot.setChangedFiles(List.of(testFile));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreNonJavaProductionFiles() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename(
            "src/main/resources/application.yml"
        );
        file.setStatus("modified");

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldHandleMultipleProductionChanges() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile serviceFile =
            new ChangeSnapshot.ChangedFile();

        serviceFile.setFilename(
            "src/main/java/com/releaseguard/service/UserService.java"
        );
        serviceFile.setStatus("modified");

        ChangeSnapshot.ChangedFile controllerFile =
            new ChangeSnapshot.ChangedFile();

        controllerFile.setFilename(
            "src/main/java/com/releaseguard/controller/UserController.java"
        );
        controllerFile.setStatus("modified");

        snapshot.setChangedFiles(
            List.of(
                serviceFile,
                controllerFile
            )
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(2, findings.size());
    }

    @Test
    void shouldHandleMultipleProductionChangesWithOneTest() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile serviceFile =
            new ChangeSnapshot.ChangedFile();

        serviceFile.setFilename(
            "src/main/java/com/releaseguard/service/UserService.java"
        );
        serviceFile.setStatus("modified");

        ChangeSnapshot.ChangedFile controllerFile =
            new ChangeSnapshot.ChangedFile();

        controllerFile.setFilename(
            "src/main/java/com/releaseguard/controller/UserController.java"
        );
        controllerFile.setStatus("modified");

        ChangeSnapshot.ChangedFile serviceTestFile =
            new ChangeSnapshot.ChangedFile();

        serviceTestFile.setFilename(
            "src/test/java/com/releaseguard/service/UserServiceTest.java"
        );
        serviceTestFile.setStatus("modified");

        snapshot.setChangedFiles(
            List.of(
                serviceFile,
                controllerFile,
                serviceTestFile
            )
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());

        assertEquals(
            "src/main/java/com/releaseguard/controller/UserController.java",
            findings.get(0).filePath()
        );
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

    @Test
    void shouldReturnEmptyWhenThereAreNoChangedFiles() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        snapshot.setChangedFiles(List.of());

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }
}
