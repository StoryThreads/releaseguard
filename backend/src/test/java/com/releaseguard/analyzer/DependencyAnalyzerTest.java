package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DependencyAnalyzerTest {

    private final DependencyAnalyzer analyzer = new DependencyAnalyzer();

    @Test
    void shouldDetectPomDependencyChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("pom.xml");
        file.setStatus("modified");
        file.setPatch("""
            @@ -10,6 +10,7 @@
             <dependencies>
            +    <dependency>
            +        <groupId>org.example</groupId>
            +        <artifactId>example-library</artifactId>
            +        <version>1.0.0</version>
            +    </dependency>
             </dependencies>
            """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());

        assertEquals(
            "DEP-001",
            findings.get(0).ruleId()
        );

        assertEquals(
            AnalyzerType.DEPENDENCY,
            findings.get(0).analyzerType()
        );

        assertEquals(
            "pom.xml",
            findings.get(0).filePath()
        );
    }

    @Test
    void shouldDetectPackageJsonDependencyChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("package.json");
        file.setStatus("modified");
        file.setPatch("""
            @@ -5,6 +5,7 @@
             "dependencies": {
            +    "example-package": "^1.0.0"
             }
            """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());

        assertEquals(
            "DEP-001",
            findings.get(0).ruleId()
        );
    }

    @Test
    void shouldDetectGradleDependencyChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("build.gradle");
        file.setStatus("modified");
        file.setPatch("""
            @@ -10,6 +10,7 @@
             dependencies {
            +    implementation 'org.example:example-library:1.0.0'
             }
            """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("DEP-001", findings.get(0).ruleId());
    }

    @Test
    void shouldIgnoreNonDependencyFile() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("src/main/java/Test.java");
        file.setStatus("modified");
        file.setPatch("""
            @@ -1,3 +1,4 @@
             public class Test {
            +    private String value;
             }
            """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldReturnEmptyWhenNoChangedFiles() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        snapshot.setChangedFiles(List.of());

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

    @Test
    void shouldIgnoreEmptyPatch() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("pom.xml");
        file.setStatus("modified");
        file.setPatch("");

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreGitDiffMetadataLines() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("pom.xml");
        file.setStatus("modified");
        file.setPatch("""
            --- a/pom.xml
            +++ b/pom.xml
            @@ -1,3 +1,3 @@
             <project>
             </project>
            """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }
}
