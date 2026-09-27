package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CodeAnalyzerTest {

    private final CodeAnalyzer analyzer = new CodeAnalyzer();

    @Test
    void shouldDetectDebugPrint() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            """
            @@ -1,2 +1,3 @@
            +System.out.println("debug");
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("CODE-001", findings.getFirst().ruleId());
        assertEquals(FindingSeverity.MEDIUM, findings.getFirst().severity());
    }

    @Test
    void shouldDetectTodo() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            """
            @@ -1,2 +1,3 @@
            +// TODO: improve validation
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("CODE-002", findings.getFirst().ruleId());
        assertEquals(FindingSeverity.LOW, findings.getFirst().severity());
    }

    @Test
    void shouldDetectFixme() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            """
            @@ -1,2 +1,3 @@
            +// FIXME: handle this properly
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("CODE-002", findings.getFirst().ruleId());
    }

    @Test
    void shouldDetectEmptyCatchBlock() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            """
            @@ -1,4 +1,6 @@
            +try {
            +    doSomething();
            +} catch (Exception e) {
            +}
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("CODE-003", findings.getFirst().ruleId());
        assertEquals(FindingSeverity.HIGH, findings.getFirst().severity());
    }

    @Test
    void shouldIgnoreNonCodeFiles() {

        ChangeSnapshot snapshot = createSnapshot(
            "README.md",
            """
            @@ -1,2 +1,3 @@
            +System.out.println("debug");
            +TODO: something
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreNullSnapshot() {

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(null)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreFileWithoutPatch() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            null
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldDetectMultipleIssues() {

        ChangeSnapshot snapshot = createSnapshot(
            "src/main/java/com/example/Test.java",
            """
            @@ -1,5 +1,10 @@
            +System.out.println("debug");
            +// TODO: refactor
            +try {
            +    doSomething();
            +} catch (Exception e) {
            +}
            """
        );

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(3, findings.size());

        assertTrue(
            findings.stream()
                .anyMatch(f -> f.ruleId().equals("CODE-001"))
        );

        assertTrue(
            findings.stream()
                .anyMatch(f -> f.ruleId().equals("CODE-002"))
        );

        assertTrue(
            findings.stream()
                .anyMatch(f -> f.ruleId().equals("CODE-003"))
        );
    }

    private ChangeSnapshot createSnapshot(
        String filename,
        String patch
    ) {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile changedFile =
            new ChangeSnapshot.ChangedFile();

        changedFile.setFilename(filename);
        changedFile.setPatch(patch);

        snapshot.setChangedFiles(List.of(changedFile));

        return snapshot;
    }
}
