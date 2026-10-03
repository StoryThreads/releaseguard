# ReleaseGuard V0.5.7 — Prediction Service

## Architecture

Spring Boot builds the raw `ChangeSnapshot + Findings` contract and calls:

`POST /api/v1/predict`

The Python service:

1. validates the request;
2. maps the Java contract into the Python input contract;
3. extracts the V0.5.1 feature vector;
4. applies the V0.5.1 deterministic normalizer;
5. loads the versioned XGBoost artifact;
6. produces class probabilities;
7. derives the risk level;
8. derives a 0–100 numerical risk score;
9. returns model, feature and dataset versions.

Spring Boot then persists the feature vector and prediction against the analyzed change.

## Development service

From `ai-service`:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health:

```text
GET http://localhost:8000/health
```

Prediction:

```text
POST http://localhost:8000/api/v1/predict
```

## Model artifact

The active production artifact is:

```text
artifacts/models/xgboost/2.0.0/
```

- Model Name: `xgboost`
- Model Version: `2.0.0`
- Feature Version: `1.0.0`
- Dataset Version: `2.0.0`

It is trained from real data using the V0.5.1 feature-extraction and normalization pipeline, promoted via `scripts/promote_real_model.py`. The legacy synthetic development artifact remains archived under `artifacts/models/xgboost/1.0.0/`.

## Risk score

The score is the probability-weighted expected risk level:

- LOW = 25
- MEDIUM = 50
- HIGH = 75
- CRITICAL = 100

This score is a ReleaseGuard application-level numerical representation, not a calibrated probability of production failure.

## Backend

Configure:

```text
ML_SERVICE_URL=http://localhost:8000
```

The backend calls the Python service after deterministic analyzers complete and persists the returned prediction and feature vector in `ml_predictions`.
