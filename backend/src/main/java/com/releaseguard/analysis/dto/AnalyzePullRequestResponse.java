package com.releaseguard.analysis.dto;

import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;

import java.util.List;

public class AnalyzePullRequestResponse {

    private ChangeSnapshot snapshot;

    private Long changeId;

    private List<Finding> findings;

    public AnalyzePullRequestResponse() {
    }

    public AnalyzePullRequestResponse(
        ChangeSnapshot snapshot,
        Long changeId,
        List<Finding> findings
    ) {
        this.snapshot = snapshot;
        this.changeId = changeId;
        this.findings = findings;
    }

    public ChangeSnapshot getSnapshot() {
        return snapshot;
    }

    public void setSnapshot(ChangeSnapshot snapshot) {
        this.snapshot = snapshot;
    }

    public Long getChangeId() {
        return changeId;
    }

    public void setChangeId(Long changeId) {
        this.changeId = changeId;
    }

    public List<Finding> getFindings() {
        return findings;
    }

    public void setFindings(List<Finding> findings) {
        this.findings = findings;
    }
}
