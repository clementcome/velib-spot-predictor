"""Definition of backend routes."""
from typing import Annotated, Dict

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sklearn.base import RegressorMixin

from velib_spot_predictor.api.model import PredictionInput, PredictionOutput
from velib_spot_predictor.model.predict_model import load_model

router = APIRouter()


class ModelManager:
    """Class used to manage the model loading."""

    def __init__(self):
        """Initialize the model manager."""
        self.model = None

    def get_model(self) -> RegressorMixin:
        """Get the model, load it if it is not already loaded."""
        if self.model is None:
            try:
                self.model = load_model("models/model.joblib")
            except FileNotFoundError:
                pass
        return self.model


model_manager = ModelManager()


@router.get("/")
async def root() -> Dict[str, str]:
    """Root route of the backend, returns a welcome message.

    Returns
    -------
    Dict[str, str]
        "message": Welcome message
    """
    return {"message": "Welcome to the velib spot predictor API"}


@router.post("/predict")
async def predict(
    prediction_input: PredictionInput,
    model: Annotated[RegressorMixin, Depends(model_manager.get_model)],
) -> PredictionOutput:
    """Predicts the probability of a velib spot being available.

    Parameters
    ----------
    prediction_input : PredictionInput
        Input data for the prediction, id_station, hour and minute

    Returns
    -------
    PredictionOutput
        Output data for the prediction, id_station and probability
    """
    if model is None:
        raise HTTPException(
            status_code=400,
            detail="Could not load model, sorry for the inconvenience.",
        )
    input_array = np.array(
        [
            [
                prediction_input.id_station,
                prediction_input.hour + prediction_input.minute / 60,
            ]
        ]
    )
    predicted_spots = model.predict(input_array)
    prediction_output = PredictionOutput(
        id_station=prediction_input.id_station,
        prediction=predicted_spots[0],
    )
    return prediction_output
