package com.releaseguard.ml.dto;

import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;

import java.util.List;

public class MlPredictionRequest {

    private ChangeSnapshot changeSnapshot;
    private List<Finding> findings;

    public MlPredictionRequest() {
    }

    public MlPredictionRequest(
        ChangeSnapshot changeSnapshot,
        List<Finding> findings
    ) {
        this.changeSnapshot = changeSnapshot;
        this.findings = findings;
    }

    public ChangeSnapshot getChangeSnapshot() {
        return changeSnapshot;
    }

    public void setChangeSnapshot(ChangeSnapshot changeSnapshot) {
        this.changeSnapshot = changeSnapshot;
    }

    public List<Finding> getFindings() {
        return findings;
    }

    public void setFindings(List<Finding> findings) {
        this.findings = findings;
    }
}
