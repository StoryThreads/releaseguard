package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AnalyzerEngineTest {

    @Test
    void shouldRunAllRegisteredAnalyzers() {

        Analyzer analyzerOne = new TestAnalyzer(
            AnalyzerType.CODE,
            List.of(
                new Finding(
                    AnalyzerType.CODE,
                    FindingType.CODE_ISSUE,
                    FindingSeverity.LOW,
                    "TEST-001",
                    "Test finding one",
                    "Test message one",
                    "Test.java",
                    null
                )
            )
        );

        Analyzer analyzerTwo = new TestAnalyzer(
            AnalyzerType.DEPENDENCY,
            List.of(
                new Finding(
                    AnalyzerType.DEPENDENCY,
                    FindingType.DEPENDENCY_ISSUE,
                    FindingSeverity.MEDIUM,
                    "TEST-002",
                    "Test finding two",
                    "Test message two",
                    "pom.xml",
                    null
                )
            )
        );

        AnalyzerEngine engine = new AnalyzerEngine(
            List.of(analyzerOne, analyzerTwo)
        );

        ChangeSnapshot snapshot = new ChangeSnapshot();

        List<Finding> findings = engine.analyze(
            new AnalyzerContext(snapshot)
        );

        assertEquals(2, findings.size());
        assertEquals("TEST-001", findings.get(0).ruleId());
        assertEquals("TEST-002", findings.get(1).ruleId());
    }

    @Test
    void shouldReturnEmptyListWhenContextIsNull() {

        Analyzer analyzer = new TestAnalyzer(
            AnalyzerType.CODE,
            List.of(
                new Finding(
                    AnalyzerType.CODE,
                    FindingType.CODE_ISSUE,
                    FindingSeverity.LOW,
                    "TEST-001",
                    "Test finding",
                    "Test message",
                    "Test.java",
                    null
                )
            )
        );

        AnalyzerEngine engine = new AnalyzerEngine(
            List.of(analyzer)
        );

        List<Finding> findings = engine.analyze(null);

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldHandleAnalyzerReturningNull() {

        Analyzer analyzer = new TestAnalyzer(
            AnalyzerType.CODE,
            null
        );

        AnalyzerEngine engine = new AnalyzerEngine(
            List.of(analyzer)
        );

        ChangeSnapshot snapshot = new ChangeSnapshot();

        List<Finding> findings = engine.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    @Test
    void shouldIgnoreNullAnalyzer() {

        List<Analyzer> analyzers = new java.util.ArrayList<>();
        analyzers.add(null);

        AnalyzerEngine engine = new AnalyzerEngine(analyzers);

        ChangeSnapshot snapshot = new ChangeSnapshot();

        List<Finding> findings = engine.analyze(
            new AnalyzerContext(snapshot)
        );

        assertTrue(findings.isEmpty());
    }

    private static class TestAnalyzer implements Analyzer {

        private final AnalyzerType type;
        private final List<Finding> findings;

        private TestAnalyzer(
            AnalyzerType type,
            List<Finding> findings
        ) {
            this.type = type;
            this.findings = findings;
        }

        @Override
        public AnalyzerType getType() {
            return type;
        }

        @Override
        public List<Finding> analyze(AnalyzerContext context) {
            return findings;
        }
    }
}
