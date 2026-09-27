package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;

public record AnalyzerContext(
    ChangeSnapshot changeSnapshot
) {
}
