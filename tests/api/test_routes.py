import numpy as np
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sklearn.base import RegressorMixin

import velib_spot_predictor.api.prediction.routes as routes
from velib_spot_predictor.api import app


def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the velib spot predictor API"
    }


@pytest.fixture
def mock_load_model_ok(mocker: MockerFixture):
    mock_model = mocker.Mock()
    mock_model.predict.return_value = np.array([1.5])
    mock_load_model = mocker.patch.object(
        routes, "load_model", return_value=mock_model
    )
    return mock_load_model


@pytest.fixture
def mock_load_model_error(mocker: MockerFixture):
    mock_load_model = mocker.patch.object(
        routes, "load_model", side_effect=FileNotFoundError
    )
    return mock_load_model


class TestPredict:
    def setup_method(self):
        routes.model_manager = routes.ModelManager()

    def test_predict_error(self, mock_load_model_error):
        client = TestClient(app)
        response = client.post(
            "/predict",
            json={
                "id_station": 10042,
                "hour": 10,
                "minute": 30,
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Could not load model, sorry for the inconvenience."
        }

    def test_predict_ok(self, mock_load_model_ok):
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


class TestModelManager:
    def setup_method(self):
        self.model_manager = routes.ModelManager()

    def test_get_model_ok(self, mock_load_model_ok):
        assert self.model_manager.get_model() is not None

    def test_get_model_none(self, mock_load_model_error):
        assert self.model_manager.get_model() is None
