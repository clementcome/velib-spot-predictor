import os

import pytest
from pydantic import ValidationError

from velib_spot_predictor.environment import AWSConfig, S3AWSConfig


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear environment variables that might affect tests."""
    for key in list(os.environ.keys()):
        if key.startswith("AWS_") or key.startswith("S3_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def empty_env_file(tmp_path):
    """Set an empty .env file by default."""
    empty_env_file = tmp_path / "empty.env"
    empty_env_file.write_text("")
    return empty_env_file


class TestAWSConfig:
    def test_check_credentials_should_raise_error_if_access_key_id_provided_without_secret_key(
        self, empty_env_file
    ):
        # Given
        data = {"AWS_ACCESS_KEY_ID": "fake_access_key"}

        # When / Then
        with pytest.raises(ValidationError):
            AWSConfig(**data, _env_file=empty_env_file)

    def test_get_client_should_use_provided_credentials(
        self, mocker, empty_env_file
    ):
        # Given
        data = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "REGION_NAME": "eu-west-3",
        }
        config = AWSConfig(**data, _env_file=empty_env_file)
        mock_boto_client = mocker.patch(
            "boto3.client", return_value="mock_client"
        )

        # When
        client = config.get_client("s3")

        # Then
        mock_boto_client.assert_called_with(
            "s3",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="eu-west-3",
        )
        assert client == "mock_client"

    def test_get_client_should_use_default_credentials_if_no_access_key(
        self, mocker, empty_env_file
    ):
        # Given
        data = {"REGION_NAME": "eu-west-3"}
        config = AWSConfig(**data, _env_file=empty_env_file)
        mock_boto_client = mocker.patch(
            "boto3.client", return_value="mock_client"
        )

        # When
        client = config.get_client("s3")

        # Then
        mock_boto_client.assert_called_with("s3", region_name="eu-west-3")
        assert client == "mock_client"


class TestS3AWSConfig:
    def test_s3awsconfig_should_inherit_awsconfig(self):
        # Given
        data = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "REGION_NAME": "eu-west-3",
            "VELIB_RAW_BUCKET": "clement-velib-raw-automation",
        }

        # When
        config = S3AWSConfig(**data)

        # Then
        assert config.AWS_ACCESS_KEY_ID == "fake_access_key"
        assert config.AWS_SECRET_ACCESS_KEY == "fake_secret_key"
        assert config.REGION_NAME == "eu-west-3"
        assert config.VELIB_RAW_BUCKET == "clement-velib-raw-automation"

    def test_s3awsconfig_should_use_provided_credentials(self, mocker):
        # Given
        data = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "REGION_NAME": "eu-west-3",
            "VELIB_RAW_BUCKET": "clement-velib-raw-automation",
        }
        config = S3AWSConfig(**data)
        mock_boto_client = mocker.patch(
            "boto3.client", return_value="mock_client"
        )

        # When
        client = config.get_client()

        # Then
        mock_boto_client.assert_called_with(
            "s3",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="eu-west-3",
        )
        assert client == "mock_client"
