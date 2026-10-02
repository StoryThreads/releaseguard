# ReleaseGuard Model Versioning

## Purpose

ReleaseGuard ML artifacts are versioned so that every prediction can be
traced to the exact model, feature schema, and dataset used during training.

The model versioning contract applies to all ReleaseGuard ML candidates.

---

## Version Components

Every trained model artifact must contain the following metadata:

- `model_name`
- `model_version`
- `feature_version`
- `dataset_version`

These values are persisted in `metadata.json`.

### Example

```json
{
  "model_name": "logistic_regression_baseline",
  "model_version": "1.0.0",
  "feature_version": "1.0.0",
  "dataset_version": "1.0.0"
}