import numpy as np
from sklearn.base import RegressorMixin

from velib_spot_predictor.api import app
from velib_spot_predictor.api.model import PredictionInput
from velib_spot_predictor.model.predict_model import load_model

model: RegressorMixin = load_model("models/model.joblib")


@app.get("/")
async def root():
    return {"message": "Welcome to the velib spot predictor API"}


@app.post("/predict")
async def predict(prediction_input: PredictionInput):
    input_array = np.array(
        [
            [
                prediction_input.id_station,
                prediction_input.hour + prediction_input.minute / 60,
            ]
        ]
    )
    prediction_output = model.predict(input_array)
    return {"message": float(prediction_output)}
