import json

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from velib_spot_predictor.data.load_data import (
    load_prepared,
    load_station_information,
)


def test_load_prepared(mocker: MockerFixture):
    mock_read = mocker.patch.object(pd, "read_pickle")

    load_prepared("fake_path")

    mock_read.assert_called_once_with("fake_path")


def test_load_station_information(mocker: MockerFixture):
    station_information_json = {
        "data": {
            "stations": [
                {
                    "station_id": 213688169,
                    "name": "Benjamin Godard - Victor Hugo",
                    "lat": 48.865983,
                    "lon": 2.275725,
                    "capacity": 35,
                    "stationCode": "16107",
                },
                {
                    "station_id": 653222953,
                    "name": "Mairie de Rosny-sous-Bois",
                    "lat": 48.871256519012,
                    "lon": 2.4865807592869,
                    "capacity": 30,
                    "stationCode": "31104",
                    "rental_methods": ["CREDITCARD"],
                },
                {
                    "station_id": 17278902806,
                    "name": "Rouget de L'isle - Watteau",
                    "lat": 48.778192750803,
                    "lon": 2.3963020229163,
                    "capacity": 20,
                    "stationCode": "44015",
                },
            ]
        }
    }
    mocker.patch("builtins.open", mocker.mock_open())
    mock_json_load = mocker.patch.object(json, "load")
    mock_json_load.return_value = station_information_json

    station_information = load_station_information("fake_path")
    mock_json_load.assert_called_once()

    assert "station_id" in station_information.columns
    assert set(station_information["station_id"]) == {
        213688169,
        653222953,
        17278902806,
    }
