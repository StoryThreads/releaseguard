# ReleaseGuard AI Service

Machine Learning & Risk Analysis microservice for ReleaseGuard.

## Production Model Summary
- **Model**: XGBoost Multiclass Classifier
- **Model Version**: `2.0.0`
- **Dataset Version**: `2.0.0` (Real GitHub PRs & Post-Merge Defect Signals)
- **Feature Version**: `1.0.0` (28 normalized features)
- **Production Artifact**: `artifacts/models/xgboost/2.0.0/model.joblib`
- **Production Metadata**: `artifacts/models/xgboost/2.0.0/metadata.json`
- **Promotion Manifest**: `data/real/manifests/production_model_promotion_manifest.json`
- **Model SHA-256**: `1322851a2fcd2815f27fa38dabf97deb47e616f91b82ca1e1b9bc51d541f415b`

---

## Unified CLI

ReleaseGuard provides a single CLI entry point using standard Python `argparse`:

```bash
# 1. Environment and version summary
python -m app.cli info
# or shortcut:
python scripts/run.py info

# 2. Pipeline state validation & integrity check
python -m app.cli pipeline validate

# 3. Start the FastAPI runtime server
python -m app.cli serve [--host 0.0.0.0] [--port 8000] [--reload]
```

### Pipeline Workflow Commands
All pipeline stages are protected by pre-flight and post-flight state validation:
```bash
# Collect real PRs and defect signals
python -m app.cli pipeline collect [--limit 100]

# Build labels, features, splits, and freeze dataset
python -m app.cli pipeline dataset

# Train models on frozen splits
python -m app.cli pipeline train [--version 2.0.0]

# Evaluate trained models on test split
python -m app.cli pipeline evaluate [--version 2.0.0]

# Promote candidate model to production artifact
python -m app.cli pipeline promote [--version 2.0.0]

# Full model retraining flow (train -> evaluate -> promote)
python -m app.cli pipeline run-all [--version 2.0.0]
```

---

## Testing
Run the complete test suite:
```bash
pytest
```
Currently: **192 tests, 0 failures, 0 errors**.