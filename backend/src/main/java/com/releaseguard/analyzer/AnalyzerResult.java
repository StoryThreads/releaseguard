package com.releaseguard.analyzer;

import java.util.List;

public record AnalyzerResult(
    AnalyzerType analyzerType,
    List<Finding> findings
) {
}
