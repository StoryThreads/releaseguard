from fastapi import FastAPI, HTTPException

from app.prediction.schemas import (
    PredictionRequest,
    PredictionResponse,
)
from app.prediction.service import PredictionService


APP_VERSION = "0.5.8"

app = FastAPI(
    title="ReleaseGuard AI Service",
    version=APP_VERSION,
)


def _load_prediction_service() -> PredictionService:
    try:
        return PredictionService.from_artifact()
    except Exception as exc:
        raise RuntimeError(
            "Failed to load ReleaseGuard production "
            f"model artifact: {exc}"
        ) from exc


prediction_service = _load_prediction_service()


@app.get("/health")
def health() -> dict:
    """
    Health endpoint exposing the exact versions used by
    the loaded production model.
    """

    return {
        "status": "UP",
        "service_version": APP_VERSION,
        "model_name": prediction_service.metadata[
            "model_name"
        ],
        "model_version": prediction_service.metadata[
            "model_version"
        ],
        "feature_version": prediction_service.metadata[
            "feature_version"
        ],
        "dataset_version": prediction_service.metadata[
            "dataset_version"
        ],
    }


@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
) -> PredictionResponse:
    try:
        return prediction_service.predict(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed.",
        ) from exc