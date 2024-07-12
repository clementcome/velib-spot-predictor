"""Backend for predicting velib availability."""

from typing import Dict

from fastapi import FastAPI

from velib_spot_predictor.api.database.routes import router as database_router
from velib_spot_predictor.api.prediction.routes import (
    router as prediction_router,
)

app = FastAPI()
app.include_router(prediction_router)
app.include_router(database_router)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root route of the backend, returns a welcome message.

    Returns
    -------
    Dict[str, str]
        "message": Welcome message
    """
    return {"message": "Welcome to the velib spot predictor API"}
