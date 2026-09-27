package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
class AnalyzerEngineSpringTest {

    @Autowired
    private AnalyzerEngine analyzerEngine;

    @Autowired
    private CodeAnalyzer codeAnalyzer;

    @Test
    void shouldLoadAnalyzerEngineAndCodeAnalyzer() {

        assertNotNull(analyzerEngine);
        assertNotNull(codeAnalyzer);
    }

    @Test
    void shouldExecuteRegisteredAnalyzers() {

        ChangeSnapshot snapshot = new ChangeSnapshot();

        List<Finding> findings = analyzerEngine.analyze(
            new AnalyzerContext(snapshot)
        );

        assertNotNull(findings);
        assertTrue(findings.isEmpty());
    }
}
