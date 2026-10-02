package com.releaseguard.ml.dto;

import com.fasterxml.jackson.annotation.JsonAlias;

import java.util.Map;

public class MlPredictionResponse {

    @JsonAlias("risk_level")
    private String riskLevel;

    @JsonAlias("risk_score")
    private double riskScore;

    @JsonAlias("class_probabilities")
    private Map<String, Double> classProbabilities;

    @JsonAlias("feature_vector")
    private Map<String, Double> featureVector;

    @JsonAlias("model_name")
    private String modelName;

    @JsonAlias("model_version")
    private String modelVersion;

    @JsonAlias("feature_version")
    private String featureVersion;

    @JsonAlias("dataset_version")
    private String datasetVersion;

    public MlPredictionResponse() {
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public double getRiskScore() {
        return riskScore;
    }

    public void setRiskScore(double riskScore) {
        this.riskScore = riskScore;
    }

    public Map<String, Double> getClassProbabilities() {
        return classProbabilities;
    }

    public void setClassProbabilities(
        Map<String, Double> classProbabilities
    ) {
        this.classProbabilities = classProbabilities;
    }

    public Map<String, Double> getFeatureVector() {
        return featureVector;
    }

    public void setFeatureVector(
        Map<String, Double> featureVector
    ) {
        this.featureVector = featureVector;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public void setModelVersion(String modelVersion) {
        this.modelVersion = modelVersion;
    }

    public String getFeatureVersion() {
        return featureVersion;
    }

    public void setFeatureVersion(String featureVersion) {
        this.featureVersion = featureVersion;
    }

    public String getDatasetVersion() {
        return datasetVersion;
    }

    public void setDatasetVersion(String datasetVersion) {
        this.datasetVersion = datasetVersion;
    }
}
