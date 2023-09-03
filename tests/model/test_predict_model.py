import pytest
from pytest_mock import MockerFixture

from velib_spot_predictor.model.predict_model import load_model


def test_load_model(mocker: MockerFixture):
    mock_load = mocker.patch(
        "velib_spot_predictor.model.predict_model.load", return_value="model"
    )
    model = load_model("model_path")
    assert model == "model"
    mock_load.assert_called_once_with("model_path")
