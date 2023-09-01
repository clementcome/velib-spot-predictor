import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

import velib_spot_predictor.api.routes as routes
from velib_spot_predictor.api import app


def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the velib spot predictor API"
    }


def test_predict():
    client = TestClient(app)
    response = client.post(
        "/predict",
        json={
            "id_station": 10042,
            "hour": 10,
            "minute": 30,
        },
    )
    assert response.status_code == 200
    assert response.json()["id_station"] == 10042
    assert response.json()["prediction"] >= 0
