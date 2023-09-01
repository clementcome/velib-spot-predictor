"""Definition of backend routes."""
from typing import Dict

import numpy as np
from sklearn.base import RegressorMixin

from velib_spot_predictor.api import app
from velib_spot_predictor.api.model import PredictionInput, PredictionOutput
from velib_spot_predictor.model.predict_model import load_model

model: RegressorMixin = load_model("models/model.joblib")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root route of the backend, returns a welcome message.

    Returns
    -------
    Dict[str, str]
        "message": Welcome message
    """
    return {"message": "Welcome to the velib spot predictor API"}


@app.post("/predict")
async def predict(prediction_input: PredictionInput) -> PredictionOutput:
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
    input_array = np.array(
        [
            [
                prediction_input.id_station,
                prediction_input.hour + prediction_input.minute / 60,
            ]
        ]
    )
    predicted_probability = model.predict(input_array)
    prediction_output = PredictionOutput(
        id_station=prediction_input.id_station,
        probability=predicted_probability,
    )
    return prediction_output
