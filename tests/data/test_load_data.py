import pandas as pd
import pytest
from pytest_mock import MockerFixture

from velib_spot_predictor.data.load_data import load_raw


def test_load_raw(mocker: MockerFixture):
    mock_data = pd.DataFrame(
        {
            "Actualisation de la donnée": [
                "2021-01-01 12:00:00+00:00",
                "2021-01-01 12:15:00+00:00",
                "2021-01-01 12:30:00+00:00",
                "2021-01-01 12:45:00+00:00",
            ],
            "Heure": [12.0, 12.25, 12.5, 12.75],
        }
    )
    mock_read = mocker.patch.object(pd, "read_csv")
    mock_read.return_value = mock_data

    data = load_raw("fake_path")

    mock_read.assert_called_once_with("fake_path", sep=";")
    pd.testing.assert_frame_equal(data, mock_data)
    assert (
        data["Actualisation de la donnée"].dtype
        == "datetime64[ns, Europe/Paris]"
    )
