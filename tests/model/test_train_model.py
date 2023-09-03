import pandas as pd
import pytest
from pytest_mock import MockFixture

from velib_spot_predictor.model.train_model import Model, train


def test_train_model(mocker: MockFixture):
    # Given
    mock_data = pd.DataFrame(
        {
            "Identifiant station": [1, 2, 3],
            "Heure": [1, 2, 3],
            "Nombre bornettes libres": [1, 2, 3],
        }
    )
    mock_fit = mocker.patch.object(Model, "fit")

    # When
    model = train(mock_data)

    # Then
    mock_fit.assert_called_once()
