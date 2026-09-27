package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DatabaseAnalyzerTest {

    private final DatabaseAnalyzer analyzer = new DatabaseAnalyzer();

    @Test
    void shouldDetectCreateTable() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("V2__create_users.sql");
        file.setStatus("added");
        file.setPatch("""
                @@ -0,0 +1,5 @@
                +CREATE TABLE users (
                +    id BIGINT PRIMARY KEY,
                +    username VARCHAR(100) NOT NULL
                +);
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("DB-001", findings.get(0).ruleId());
        assertEquals(
            AnalyzerType.DATABASE,
            findings.get(0).analyzerType()
        );
        assertEquals(
            "V2__create_users.sql",
            findings.get(0).filePath()
        );
    }

    @Test
    void shouldDetectAlterTable() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("V3__add_email.sql");
        file.setStatus("added");
        file.setPatch("""
                @@ -0,0 +1 @@
                +ALTER TABLE users ADD COLUMN email VARCHAR(255);
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("DB-001", findings.get(0).ruleId());
    }

    @Test
    void shouldDetectDropTable() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("V4__remove_legacy.sql");
        file.setStatus("modified");
        file.setPatch("""
                @@ -1,2 +1,2 @@
                -DROP TABLE legacy_users;
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
        assertEquals("DB-001", findings.get(0).ruleId());
    }

    @Test
    void shouldDetectCreateIndex() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("V5__add_user_index.sql");
        file.setStatus("added");
        file.setPatch("""
                @@ -0,0 +1 @@
                +CREATE INDEX idx_users_email ON users(email);
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(1, findings.size());
    }

    @Test
    void shouldIgnoreNonSqlFile() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("User.java");
        file.setStatus("modified");
        file.setPatch("""
                @@ -1,2 +1,3 @@
                +CREATE TABLE users (
                +    id BIGINT
                +);
                """);

        snapshot.setChangedFiles(List.of(file));

        List<Finding> findings = analyzer.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreUnrelatedSqlChange() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        ChangeSnapshot.ChangedFile file =
            new ChangeSnapshot.ChangedFile();

        file.setFilename("V6__update_data.sql");
        file.setStatus("modified");
        file.setPatch("""
                @@ -1,2 +1,2 @@
                +UPDATE users SET active = true;
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

        file.setFilename("V7__schema.sql");
        file.setStatus("modified");
        file.setPatch("""
                --- a/V7__schema.sql
                +++ b/V7__schema.sql
                @@ -1,3 +1,3 @@
                 SELECT 1;
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
