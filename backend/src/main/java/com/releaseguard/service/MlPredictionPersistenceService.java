package com.releaseguard.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.releaseguard.entity.Change;
import com.releaseguard.entity.MlPredictionEntity;
import com.releaseguard.ml.dto.MlPredictionResponse;
import com.releaseguard.repository.MlPredictionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MlPredictionPersistenceService {

    private final MlPredictionRepository repository;
    private final ObjectMapper objectMapper;

    public MlPredictionPersistenceService(
        MlPredictionRepository repository,
        ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public MlPredictionEntity save(
        Change change,
        MlPredictionResponse prediction
    ) {

        validatePrediction(prediction);

        MlPredictionEntity entity =
            repository.findByChangeId(change.getId())
                .orElseGet(MlPredictionEntity::new);

        entity.setChange(change);

        entity.setRiskLevel(
            prediction.getRiskLevel()
        );

        entity.setRiskScore(
            prediction.getRiskScore()
        );

        entity.setClassProbabilities(
            writeJson(
                prediction.getClassProbabilities()
            )
        );

        entity.setFeatureVector(
            writeJson(
                prediction.getFeatureVector()
            )
        );

        entity.setModelName(
            prediction.getModelName()
        );

        entity.setModelVersion(
            prediction.getModelVersion()
        );

        entity.setFeatureVersion(
            prediction.getFeatureVersion()
        );

        entity.setDatasetVersion(
            prediction.getDatasetVersion()
        );

        return repository.save(entity);
    }

    @Transactional(readOnly = true)
    public MlPredictionEntity getByChangeId(
        Long changeId
    ) {

        return repository
            .findByChangeId(changeId)
            .orElse(null);
    }

    private void validatePrediction(
        MlPredictionResponse prediction
    ) {

        if (prediction == null) {
            throw new IllegalArgumentException(
                "ML prediction response must not be null"
            );
        }

        if (prediction.getRiskLevel() == null
            || prediction.getRiskLevel().isBlank()) {

            throw new IllegalStateException(
                "ML prediction response is missing riskLevel"
            );
        }

        if (prediction.getClassProbabilities() == null
            || prediction.getClassProbabilities().isEmpty()) {

            throw new IllegalStateException(
                "ML prediction response is missing class probabilities"
            );
        }

        if (prediction.getFeatureVector() == null
            || prediction.getFeatureVector().isEmpty()) {

            throw new IllegalStateException(
                "ML prediction response is missing feature vector"
            );
        }

        if (prediction.getModelName() == null
            || prediction.getModelName().isBlank()) {

            throw new IllegalStateException(
                "ML prediction response is missing model name"
            );
        }

        if (prediction.getModelVersion() == null
            || prediction.getModelVersion().isBlank()) {

            throw new IllegalStateException(
                "ML prediction response is missing model version"
            );
        }

        if (prediction.getFeatureVersion() == null
            || prediction.getFeatureVersion().isBlank()) {

            throw new IllegalStateException(
                "ML prediction response is missing feature version"
            );
        }

        if (prediction.getDatasetVersion() == null
            || prediction.getDatasetVersion().isBlank()) {

            throw new IllegalStateException(
                "ML prediction response is missing dataset version"
            );
        }

        if (prediction.getRiskScore() < 0.0
            || prediction.getRiskScore() > 100.0) {

            throw new IllegalStateException(
                "ML prediction risk score must be between 0 and 100"
            );
        }
    }

    private String writeJson(Object value) {

        try {

            return objectMapper.writeValueAsString(value);

        } catch (JsonProcessingException exception) {

            throw new IllegalStateException(
                "Failed to serialize ML prediction payload",
                exception
            );
        }
    }
}
