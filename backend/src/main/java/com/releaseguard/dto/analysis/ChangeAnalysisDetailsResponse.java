package com.releaseguard.dto.analysis;

import com.releaseguard.dto.change.ChangeResponse;
import com.releaseguard.dto.source.SourceResponse;

import java.util.List;
import java.util.Map;

public class ChangeAnalysisDetailsResponse {

    private ChangeResponse change;
    private SourceResponse source;
    private DetailedPredictionResponse prediction;
    private List<DetailedFindingResponse> findings;
    private Map<String, Long> findingsCountBySeverity;

    public ChangeAnalysisDetailsResponse() {
    }

    public ChangeAnalysisDetailsResponse(
        ChangeResponse change,
        SourceResponse source,
        DetailedPredictionResponse prediction,
        List<DetailedFindingResponse> findings,
        Map<String, Long> findingsCountBySeverity
    ) {
        this.change = change;
        this.source = source;
        this.prediction = prediction;
        this.findings = findings;
        this.findingsCountBySeverity = findingsCountBySeverity;
    }

    public ChangeResponse getChange() {
        return change;
    }

    public SourceResponse getSource() {
        return source;
    }

    public DetailedPredictionResponse getPrediction() {
        return prediction;
    }

    public List<DetailedFindingResponse> getFindings() {
        return findings;
    }

    public Map<String, Long> getFindingsCountBySeverity() {
        return findingsCountBySeverity;
    }
}
