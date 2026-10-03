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
    private List<ChangedFileResponse> files;

    public ChangeAnalysisDetailsResponse() {
    }

    public ChangeAnalysisDetailsResponse(
        ChangeResponse change,
        SourceResponse source,
        DetailedPredictionResponse prediction,
        List<DetailedFindingResponse> findings,
        Map<String, Long> findingsCountBySeverity
    ) {
        this(change, source, prediction, findings, findingsCountBySeverity, List.of());
    }

    public ChangeAnalysisDetailsResponse(
        ChangeResponse change,
        SourceResponse source,
        DetailedPredictionResponse prediction,
        List<DetailedFindingResponse> findings,
        Map<String, Long> findingsCountBySeverity,
        List<ChangedFileResponse> files
    ) {
        this.change = change;
        this.source = source;
        this.prediction = prediction;
        this.findings = findings;
        this.findingsCountBySeverity = findingsCountBySeverity;
        this.files = files != null ? files : List.of();
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

    public List<ChangedFileResponse> getFiles() {
        return files;
    }
}
