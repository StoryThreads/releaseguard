package com.releaseguard.analysis.dto;

import com.releaseguard.domain.ChangeSnapshot;

public class AnalyzePullRequestResponse {

    private ChangeSnapshot snapshot;

    public AnalyzePullRequestResponse() {
    }

    public AnalyzePullRequestResponse(ChangeSnapshot snapshot) {
        this.snapshot = snapshot;
    }

    public ChangeSnapshot getSnapshot() {
        return snapshot;
    }

    public void setSnapshot(ChangeSnapshot snapshot) {
        this.snapshot = snapshot;
    }
}
