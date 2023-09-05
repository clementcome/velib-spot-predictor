"""Environment variables configuration for the project."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3AWSConfig(BaseSettings):
    """Configuration for AWS S3."""

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    REGION_NAME: str
    VELIB_RAW_BUCKET: str = "clement-velib-raw-automation"

    model_config = SettingsConfigDict(env_file="aws.env", env_prefix="S3_")
