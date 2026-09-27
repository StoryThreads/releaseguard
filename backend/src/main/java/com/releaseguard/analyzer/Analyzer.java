package com.releaseguard.analyzer;

import java.util.List;

public interface Analyzer {

    AnalyzerType getType();

    List<Finding> analyze(AnalyzerContext context);
}
