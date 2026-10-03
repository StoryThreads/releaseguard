# Legacy Synthetic-Data Scripts

These scripts are from earlier v1 synthetic prototyping and are preserved for historical reference:
- `train_baseline.py`: Trained baseline model on synthetic data.
- `train_xgboost.py`: Trained candidate XGBoost model on synthetic data.
- `evaluate_models.py`: Evaluated v1 models on synthetic benchmarks.

## Production Pipelines
For all production real-data workflows (v2.0.0+), use the unified CLI:
```bash
python -m app.cli pipeline train
python -m app.cli pipeline evaluate
python -m app.cli pipeline promote
python -m app.cli pipeline validate
```
Or directly use the production scripts in `scripts/` (`train_real_models.py`, `evaluate_real_models.py`, `promote_real_model.py`).
