import json
import re
import shutil
from pathlib import Path

import boto3
import pytest
import requests
from click.testing import CliRunner
from pytest_mock import MockerFixture
from time_machine import travel
from velib_spot_predictor.data.constants import API_URL
from velib_spot_predictor.data.fetch import (
    IVelibRawSaver,
    LocalVelibRawSaver,
    S3VelibRawSaver,
    VelibRawExtractor,
    fetch_data,
)


class TestVelibRawExtractor:
    def setup_method(self):
        self.url = "fake_url"
        self.extractor = VelibRawExtractor(self.url)

    def test_fetch_data_ok(self, mocker: MockerFixture):
        mock_requests_get = mocker.patch.object(requests, "get")
        mock_requests_get.return_value.status_code = requests.codes.OK
        mock_requests_get.return_value.json.return_value = {
            "data": {
                "stations": [],
            }
        }
        data = self.extractor.extract()
        assert data == []
        mock_requests_get.assert_called_once_with(self.url, timeout=30)

    def test_fetch_data_error(self, mocker: MockerFixture):
        mock_requests_get = mocker.patch.object(requests, "get")
        mock_requests_get.return_value.status_code = requests.codes.NOT_FOUND
        with pytest.raises(requests.exceptions.HTTPError):
            self.extractor.extract()
        mock_requests_get.assert_called_once_with(self.url, timeout=30)


class TestIVelibRawSaver:
    class Saver(IVelibRawSaver):
        def save(self, data: list) -> None:
            pass

    @travel("2021-01-01 12:00:00")
    def test_get_filename(self):
        file_pattern = re.compile(
            r"velib_availability_real_time_[0-9]{8}-[0-9]{6}\.json"
        )
        assert re.match(file_pattern, IVelibRawSaver._get_filename())

    def test_init(self):
        saver = self.Saver()
        assert isinstance(saver.filename, str)


class TestLocalSaver:
    def test_save(self, mocker: MockerFixture):
        mock_json_dump = mocker.patch.object(json, "dump")
        saver = LocalVelibRawSaver(save_folder="test")
        # Mock the built-in open function
        mocker.patch("builtins.open", mocker.mock_open())
        saver.save([])
        mock_json_dump.assert_called_once()


class TestS3Saver:
    def test_save(self, mocker: MockerFixture):
        mock_s3_client = mocker.MagicMock()
        mocker.patch("boto3.client", return_value=mock_s3_client)
        saver = S3VelibRawSaver()
        saver.save([])
        mock_s3_client.put_object.assert_called_once()


class TestFetchData:
    def test_fetch_data_to_local(self, mocker: MockerFixture):
        mock_extractor = mocker.patch.object(
            VelibRawExtractor, "extract", return_value=[]
        )
        mock_saver = mocker.patch.object(LocalVelibRawSaver, "save")

        runner = CliRunner()
        folder_test = Path("test")
        folder_test.mkdir(exist_ok=True)

        runner.invoke(fetch_data, ["-s", str(folder_test)])

        shutil.rmtree(folder_test)

        mock_extractor.assert_called_once_with()
        mock_saver.assert_called_once_with([])

    def test_fetch_data_to_s3(self, mocker: MockerFixture):
        mock_extractor = mocker.patch.object(
            VelibRawExtractor, "extract", return_value=[]
        )
        mock_saver = mocker.patch.object(S3VelibRawSaver, "save")

        runner = CliRunner()

        runner.invoke(fetch_data, ["--s3"])

        mock_extractor.assert_called_once_with()
        mock_saver.assert_called_once_with([])
