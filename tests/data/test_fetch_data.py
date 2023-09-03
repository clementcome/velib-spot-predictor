import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import requests
from click.testing import CliRunner
from freezegun import freeze_time
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType

from velib_spot_predictor.data.constants import API_URL
from velib_spot_predictor.data.fetch_data import (
    fetch_and_save_raw_data,
    fetch_data,
)


@pytest.fixture
def mocked_open(mocker: MockerFixture):
    return mocker.patch("builtins.open", new_callable=mock_open())


def test_fetch_data_ok(mocker: MockerFixture):
    mock_requests_get = mocker.patch.object(requests, "get")
    mock_requests_get.return_value.status_code = requests.codes.OK
    mock_requests_get.return_value.json.return_value = {
        "data": {
            "stations": [],
        }
    }
    data = fetch_data("fake_url")
    assert data == []
    mock_requests_get.assert_called_once_with("fake_url", timeout=30)


def test_fetch_data_error(mocker: MockerFixture):
    mock_requests_get = mocker.patch.object(requests, "get")
    mock_requests_get.return_value.status_code = requests.codes.NOT_FOUND
    with pytest.raises(requests.exceptions.HTTPError):
        fetch_data("fake_url")
    mock_requests_get.assert_called_once_with("fake_url", timeout=30)


@freeze_time("2021-01-01 12:00:00")
def test_fetch_and_save_raw_data_ok(mocker: MockerFixture):
    mock_fetch_data = mocker.patch(
        "velib_spot_predictor.data.fetch_data.fetch_data"
    )
    mock_fetch_data.return_value = []

    mock_json_dump = mocker.patch.object(json, "dump")

    runner = CliRunner()
    result = runner.invoke(fetch_and_save_raw_data, ["data/raw"])

    expected_filepath = (
        "data/raw/velib_availability_real_time_20210101-120000.json"
    )
    mock_fetch_data.assert_called_once_with(API_URL)
    mock_json_dump.assert_called_once()
    assert mock_json_dump.call_args[0][0] == []
    assert (
        mock_json_dump.call_args[0][1].name
        == "data/raw/velib_availability_real_time_20210101-120000.json"
    )
    if Path(expected_filepath).exists():
        Path(expected_filepath).unlink()
