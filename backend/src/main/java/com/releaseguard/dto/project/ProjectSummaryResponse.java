package com.releaseguard.dto.project;

import com.releaseguard.dto.analysis.ChangeAnalysisDetailsResponse;

import java.util.List;
import java.util.Map;

public class ProjectSummaryResponse {

    private ProjectResponse project;
    private int sourcesCount;
    private int changesCount;
    private Map<String, Long> riskCounts;
    private double averageRiskScore;
    private List<ChangeAnalysisDetailsResponse> recentChanges;

    public ProjectSummaryResponse() {
    }

    public ProjectSummaryResponse(
        ProjectResponse project,
        int sourcesCount,
        int changesCount,
        Map<String, Long> riskCounts,
        double averageRiskScore,
        List<ChangeAnalysisDetailsResponse> recentChanges
    ) {
        this.project = project;
        this.sourcesCount = sourcesCount;
        this.changesCount = changesCount;
        this.riskCounts = riskCounts;
        this.averageRiskScore = averageRiskScore;
        this.recentChanges = recentChanges;
    }

    public ProjectResponse getProject() {
        return project;
    }

    public int getSourcesCount() {
        return sourcesCount;
    }

    public int getChangesCount() {
        return changesCount;
    }

    public Map<String, Long> getRiskCounts() {
        return riskCounts;
    }

    public double getAverageRiskScore() {
        return averageRiskScore;
    }

    public List<ChangeAnalysisDetailsResponse> getRecentChanges() {
        return recentChanges;
    }
}
