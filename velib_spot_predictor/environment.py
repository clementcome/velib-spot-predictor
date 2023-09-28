"""Environment variables configuration for the project."""
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class S3AWSConfig(BaseSettings):
    """Configuration for AWS S3."""

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    REGION_NAME: str
    VELIB_RAW_BUCKET: str = "clement-velib-raw-automation"

    model_config = SettingsConfigDict(env_file="aws.env", env_prefix="S3_")


class Config(BaseSettings):
    """Configuration for the project."""

    DATA_FOLDER: str = "data"
