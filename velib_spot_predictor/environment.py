"""Environment variables configuration for the project."""

from typing import Optional

import boto3
from loguru import logger
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError


class DBConfig(BaseSettings):
    """Configuration for the database."""

    HOST: str
    PORT: int = 3306
    USER: str
    PASSWORD: str
    NAME: str

    model_config = SettingsConfigDict(env_file="db.env", env_prefix="DB_")

    @property
    def db_url(self) -> str:
        """Return the database URL."""
        return f"mysql+mysqlconnector://{self.USER}:{self.PASSWORD}@{self.HOST}/{self.NAME}"

    @property
    def db_url_secured(self) -> str:
        """Return the database URL with password hidden."""
        return (
            f"mysql+mysqlconnector://{self.USER}:***@{self.HOST}/{self.NAME}"
        )

    def test_connection(self):
        """Test the connection to the database."""
        try:
            engine = create_engine(self.db_url)
            connection = engine.connect()
            connection.close()
            logger.info("Connection to {} successful", self.db_url_secured)
        except (OperationalError, ProgrammingError) as e:
            raise ConnectionError(
                f"Connection to {self.db_url_secured} failed: {e}"
            ) from e


class AWSConfig(BaseSettings):
    """Configuration for AWS.

    If ACCESS_KEY_ID is provided, SECRET_ACCESS_KEY must also be provided.
    If ACCESS_KEY_ID is not provided, default credentials will be used to get
    boto3 client.

    Examples
    --------
    Examples are written in order of priority, meaning that if you pass values,
    they will be used over the environment variables for example:
    1. Using passed values:
        >>> config = AWSConfig(
        ...     AWS_ACCESS_KEY_ID="your_access_key_id",
        ...     AWS_SECRET_ACCESS_KEY="your_secret_access_key",
        ...     AWS_SESSION_TOKEN="your_session_token",
        ...     REGION_NAME="us-east-1"
        ... )

    2. Using environment variables:
        >>> import os
        >>> os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key_id'
        >>> os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_access_key'
        >>> os.environ['AWS_SESSION_TOKEN'] = 'your_session_token'
        >>> os.environ['REGION_NAME'] = 'us-east-1'
        >>> config = AWSConfig()

    3. Using .env file (default .env or passed specific _env_file):
        Ensure you have a .env file with the following content:

        ```
        AWS_ACCESS_KEY_ID=your_access_key_id
        AWS_SECRET_ACCESS_KEY=your_secret_access_key
        AWS_SESSION_TOKEN=your_session_token
        REGION_NAME=us-east-1
        ```

        >>> config = AWSConfig()

        Or for a specific env file:
        >>> config = AWSConfig(_env_file='path/to/your/.env')

    4. Using default values:
        >>> config = AWSConfig()
        >>> # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN
        >>> # will be None, REGION_NAME will be "eu-west-3"
    """

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    REGION_NAME: Optional[str] = "eu-west-3"

    @model_validator(mode="after")
    def check_credentials(self) -> None:
        """Check if the credentials are valid."""
        if self.AWS_ACCESS_KEY_ID is not None:
            if self.AWS_SECRET_ACCESS_KEY is None:
                raise ValueError(
                    "If AWS_ACCESS_KEY_ID is provided, AWS_SECRET_ACCESS_KEY "
                    "must also be provided"
                )
            if self.AWS_SESSION_TOKEN is None:
                logger.info("Using permanent credentials")
            else:
                logger.info("Using temporary credentials")

    def get_client(self, service: str) -> boto3.client:
        """Return a boto3 client."""
        client_kwargs = {
            "region_name": self.REGION_NAME,
        }
        if self.AWS_ACCESS_KEY_ID is not None:
            client_kwargs.update(
                {
                    "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY,
                }
            )
            if self.AWS_SESSION_TOKEN is not None:
                client_kwargs["aws_session_token"] = self.AWS_SESSION_TOKEN
        return boto3.client(service, **client_kwargs)


class S3AWSConfig(AWSConfig):
    """Configuration for AWS S3.

    Environment variables should be prefixed with "S3_".
    By default the .env file is "aws.env" but you can change it by passing a
    specific _env_file.
    """

    VELIB_RAW_BUCKET: str = "clement-velib-raw-automation"

    model_config = SettingsConfigDict(env_file="aws.env", env_prefix="S3_")

    def get_client(self, service: str = "s3") -> boto3.client:
        """Return a boto3 client for S3."""
        if service != "s3":
            raise ValueError("This method is only for S3 service")
        return super().get_client(service)
