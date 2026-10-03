package com.releaseguard.dto.analysis;

public class AnalysisStatusResponse {

    private Long changeId;
    private String correlationId;
    private String status;
    private String currentStep;
    private String message;
    private Long findingsCount;
    private String riskLevel;
    private Double riskScore;

    public AnalysisStatusResponse() {
    }

    public AnalysisStatusResponse(
        Long changeId,
        String correlationId,
        String status,
        String currentStep,
        String message,
        Long findingsCount,
        String riskLevel,
        Double riskScore
    ) {
        this.changeId = changeId;
        this.correlationId = correlationId;
        this.status = status;
        this.currentStep = currentStep;
        this.message = message;
        this.findingsCount = findingsCount;
        this.riskLevel = riskLevel;
        this.riskScore = riskScore;
    }

    public Long getChangeId() {
        return changeId;
    }

    public String getCorrelationId() {
        return correlationId;
    }

    public String getStatus() {
        return status;
    }

    public String getCurrentStep() {
        return currentStep;
    }

    public String getMessage() {
        return message;
    }

    public Long getFindingsCount() {
        return findingsCount;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public Double getRiskScore() {
        return riskScore;
    }
}
