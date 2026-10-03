package com.releaseguard.dto.analysis;

import java.time.OffsetDateTime;
import java.util.Map;

public class DetailedPredictionResponse {

    private String riskLevel;
    private double riskScore;
    private Map<String, Double> classProbabilities;
    private Map<String, Object> featureVector;
    private String modelName;
    private String modelVersion;
    private String featureVersion;
    private String datasetVersion;
    private OffsetDateTime createdAt;

    public DetailedPredictionResponse() {
    }

    public DetailedPredictionResponse(
        String riskLevel,
        double riskScore,
        Map<String, Double> classProbabilities,
        Map<String, Object> featureVector,
        String modelName,
        String modelVersion,
        String featureVersion,
        String datasetVersion,
        OffsetDateTime createdAt
    ) {
        this.riskLevel = riskLevel;
        this.riskScore = riskScore;
        this.classProbabilities = classProbabilities;
        this.featureVector = featureVector;
        this.modelName = modelName;
        this.modelVersion = modelVersion;
        this.featureVersion = featureVersion;
        this.datasetVersion = datasetVersion;
        this.createdAt = createdAt;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public double getRiskScore() {
        return riskScore;
    }

    public Map<String, Double> getClassProbabilities() {
        return classProbabilities;
    }

    public Map<String, Object> getFeatureVector() {
        return featureVector;
    }

    public String getModelName() {
        return modelName;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public String getFeatureVersion() {
        return featureVersion;
    }

    public String getDatasetVersion() {
        return datasetVersion;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
