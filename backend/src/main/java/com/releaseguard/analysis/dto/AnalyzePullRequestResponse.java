package com.releaseguard.analysis.dto;

import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.ml.dto.MlPredictionResponse;

import java.util.List;

public class AnalyzePullRequestResponse {

    private ChangeSnapshot snapshot;

    private Long changeId;

    private List<Finding> findings;

    private MlPredictionResponse riskAnalysis;

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

    public AnalyzePullRequestResponse(
        ChangeSnapshot snapshot,
        Long changeId,
        List<Finding> findings,
        MlPredictionResponse riskAnalysis
    ) {
        this.snapshot = snapshot;
        this.changeId = changeId;
        this.findings = findings;
        this.riskAnalysis = riskAnalysis;
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

    public MlPredictionResponse getRiskAnalysis() {
        return riskAnalysis;
    }

    public MlPredictionResponse getPrediction() {
        return riskAnalysis;
    }

    public void setRiskAnalysis(
        MlPredictionResponse riskAnalysis
    ) {
        this.riskAnalysis = riskAnalysis;
    }

    public void setPrediction(
        MlPredictionResponse prediction
    ) {
        this.riskAnalysis = prediction;
    }
}
