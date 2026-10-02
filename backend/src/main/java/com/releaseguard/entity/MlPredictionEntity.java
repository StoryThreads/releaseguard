package com.releaseguard.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.ForeignKey;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;

@Entity
@Table(
    name = "ml_predictions",
    indexes = {
        @Index(
            name = "idx_ml_predictions_change_id",
            columnList = "change_id"
        ),
        @Index(
            name = "idx_ml_predictions_model",
            columnList = "model_name, model_version"
        )
    }
)
public class MlPredictionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "change_id",
        nullable = false,
        foreignKey = @ForeignKey(name = "fk_ml_predictions_change"),
        unique = true
    )
    private Change change;

    @Column(name = "risk_level", nullable = false, length = 20)
    private String riskLevel;

    @Column(name = "risk_score", nullable = false)
    private double riskScore;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(
        name = "class_probabilities",
        nullable = false,
        columnDefinition = "jsonb"
    )
    private String classProbabilities;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(
        name = "feature_vector",
        nullable = false,
        columnDefinition = "jsonb"
    )
    private String featureVector;

    @Column(name = "model_name", nullable = false, length = 100)
    private String modelName;

    @Column(name = "model_version", nullable = false, length = 30)
    private String modelVersion;

    @Column(name = "feature_version", nullable = false, length = 30)
    private String featureVersion;

    @Column(name = "dataset_version", nullable = false, length = 30)
    private String datasetVersion;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }

    public Long getId() {
        return id;
    }

    public Change getChange() {
        return change;
    }

    public void setChange(Change change) {
        this.change = change;
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

    public String getClassProbabilities() {
        return classProbabilities;
    }

    public void setClassProbabilities(String classProbabilities) {
        this.classProbabilities = classProbabilities;
    }

    public String getFeatureVector() {
        return featureVector;
    }

    public void setFeatureVector(String featureVector) {
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

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
