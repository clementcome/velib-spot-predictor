"""Fetch data from the Velib API and save it to a file."""

import abc
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz
import requests
from loguru import logger

from velib_spot_predictor.data.constants import TIMEZONE
from velib_spot_predictor.environment import S3AWSConfig


class VelibRawExtractor:
    """Raw data extractor for the Velib API."""

    def __init__(self, url: str):
        """Initialize the raw data extractor.

        Parameters
        ----------
        url : str
            URL of the Velib API
        """
        self.url = url

    def extract(self) -> list:
        """Extract data from the Velib API.

        Returns
        -------
        list
            List of information collected from the Velib API related to the
            availability of spots in Velib stations

        Raises
        ------
        HTTPError
            If the response status code is not 200
        """
        datetime_now = datetime.now().astimezone(tz=TIMEZONE)
        logger.info(f"Fetching data at {datetime_now}")

        response = requests.get(self.url, timeout=30)
        if response.status_code == requests.codes.OK:
            data = response.json()["data"]["stations"]
            return data
        else:
            raise requests.exceptions.HTTPError(
                f"Request failed with status code: {response.status_code}"
            )


@dataclass
class S3VelibExtractor:
    """Data extractor from an S3 bucket."""

    filepath: str
    bucket: Optional[str] = None

    def extract(self) -> list:
        """Extract data from an S3 bucket.

        Returns
        -------
        list
            List of information collected from the Velib API related to the
            availability of spots in Velib stations
        """
        s3_aws_config = S3AWSConfig()
        s3 = s3_aws_config.get_client()
        bucket = self.bucket or s3_aws_config.VELIB_RAW_BUCKET
        response = s3.get_object(Bucket=bucket, Key=self.filepath)
        return json.loads(response["Body"].read().decode("utf-8"))


class IVelibRawSaver(abc.ABC):
    """Interface for Velib raw data saver."""

    def __init__(self, timestamp: Optional[datetime] = None) -> None:
        """Initialize the Velib raw data saver."""
        self.filename = self._get_filename(timestamp)

    @staticmethod
    def _get_filename(datetime_value: Optional[datetime] = None) -> str:
        """Get the filename for the file where the data will be saved."""
        tz = pytz.timezone("Europe/Paris")
        datetime_value = datetime_value or datetime.now().astimezone(tz=tz)
        formatted_datetime = datetime_value.strftime("%Y%m%d-%H%M%S")
        return (
            f"{datetime_value:%Y/%m/%d/%H}/"
            f"velib_availability_real_time_{formatted_datetime}.json"
        )

    @abc.abstractmethod
    def save(self, data: list) -> None:
        """Save the data.

        Parameters
        ----------
        data : list
            List of information collected from the Velib API related to the
            availability of spots in Velib stations
        """
        pass


class LocalVelibRawSaver(IVelibRawSaver):
    """Velib raw data saver to a local file."""

    def __init__(self, save_folder: str) -> None:
        """Initialize the Velib raw data saver to a local file."""
        super().__init__(None)
        self.save_folder = Path(save_folder)
        self.filepath = self.save_folder / self.filename

    def save(self, data: list) -> None:
        """Save data to a local file."""
        logger.info(f"Saving fetched data to file {self.filepath}")
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w") as file:
            json.dump(data, file)


class S3VelibRawSaver(IVelibRawSaver):
    """Velib raw data saver to S3."""

    def __init__(self, timestamp: Optional[datetime] = None) -> None:
        """Initialize the Velib raw data saver to S3."""
        super().__init__(timestamp)

    def save(self, data: list) -> None:
        """Save the data as a JSON file in an S3 bucket.

        Parameters
        ----------
        data : list
            List of information collected from the Velib API related to the
            availability of spots in Velib stations
        """
        s3_aws_config = S3AWSConfig()
        s3 = s3_aws_config.get_client()
        s3.put_object(
            Body=json.dumps(data),
            Bucket=s3_aws_config.VELIB_RAW_BUCKET,
            Key=self.filename,
        )
        logger.info(f"Data saved in {self.filename}")
