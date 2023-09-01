"""Backend for predicting velib availability."""
from fastapi import FastAPI

from velib_spot_predictor.api.routes import router

app = FastAPI()
app.include_router(router)
