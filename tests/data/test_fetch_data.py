import pytest
import requests
from pytest_mock import MockerFixture

from velib_spot_predictor.data.fetch_data import fetch_data


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
