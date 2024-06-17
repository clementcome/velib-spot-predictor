import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from velib_spot_predictor.model.save_model import save_model


def test_save_model(mocker: MockerFixture):
    """Test save_model."""
    # Patch load_prepared
    mock_load_prepared = mocker.patch(
        "velib_spot_predictor.model.save_model.load_prepared",
        return_value="data",
    )
    # Patch train
    mock_train = mocker.patch(
        "velib_spot_predictor.model.save_model.train",
        return_value="model",
    )
    # Patch dump
    mock_dump = mocker.patch(
        "velib_spot_predictor.model.save_model.dump",
        return_value=None,
    )
    # Run save_model
    runner = CliRunner()
    result = runner.invoke(
        save_model,
        ["data-path", "model-path"],
    )
    # Assert
    # Assert load_prepared has been called
    mock_load_prepared.assert_called_once_with("data-path")
    # Assert train has been called
    mock_train.assert_called_once_with("data")
    # Assert dump has been called
    mock_dump.assert_called_once_with("model", "model-path")
