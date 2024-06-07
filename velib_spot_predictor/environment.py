"""Environment variables configuration for the project."""

from typing import Optional

import boto3
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSConfig(BaseSettings):
    """Configuration for AWS.

    If ACCESS_KEY_ID is provided, SECRET_ACCESS_KEY must also be provided.
    If ACCESS_KEY_ID is not provided, default credentials will be used to get
    boto3 client.
    """

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    REGION_NAME: Optional[str] = "eu-west-3"

    @model_validator(mode="after")
    def check_credentials(self) -> None:
        """Check if the credentials are valid."""
        if (
            self.AWS_ACCESS_KEY_ID is not None
            and self.AWS_SECRET_ACCESS_KEY is None
        ):
            raise ValueError(
                "If AWS_ACCESS_KEY_ID is provided, AWS_SECRET_ACCESS_KEY must "
                "also be provided"
            )

    def get_client(self, service: str) -> boto3.client:
        """Return a boto3 client."""
        if self.AWS_ACCESS_KEY_ID is not None:
            return boto3.client(
                service,
                aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                region_name=self.REGION_NAME,
            )
        return boto3.client(service, region_name=self.REGION_NAME)


class S3AWSConfig(AWSConfig):
    """Configuration for AWS S3."""

    VELIB_RAW_BUCKET: str = "clement-velib-raw-automation"

    model_config = SettingsConfigDict(env_file="aws.env", env_prefix="S3_")

    def get_client(self, service: str = "s3") -> boto3.client:
        """Return a boto3 client for S3."""
        if service != "s3":
            raise ValueError("This method is only for S3 service")
        return super().get_client(service)
