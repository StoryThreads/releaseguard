package com.releaseguard.analyzer;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class AnalyzerEngine {

    private final List<Analyzer> analyzers;

    public AnalyzerEngine(List<Analyzer> analyzers) {
        this.analyzers = analyzers;
    }

    public List<Finding> analyze(AnalyzerContext context) {

        List<Finding> findings = new ArrayList<>();

        if (context == null) {
            return findings;
        }

        for (Analyzer analyzer : analyzers) {

            if (analyzer == null) {
                continue;
            }

            List<Finding> analyzerFindings = analyzer.analyze(context);

            if (analyzerFindings != null) {
                findings.addAll(analyzerFindings);
            }
        }

        return findings;
    }
}
