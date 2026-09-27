package com.releaseguard.analyzer;

public record Finding(
    AnalyzerType analyzerType,
    FindingType findingType,
    FindingSeverity severity,
    String ruleId,
    String title,
    String message,
    String filePath,
    Integer lineNumber
) {
}
