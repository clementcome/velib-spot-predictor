"""Fetch data from the Velib API and save it to a file."""
import abc
import json
import logging
from datetime import datetime
from pathlib import Path

import boto3
import click
import pytz
import requests

from velib_spot_predictor.data.constants import API_URL
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
        self.logger = logging.getLogger(__class__.__name__)

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
        tz = pytz.timezone("Europe/Paris")
        datetime_now = datetime.now().astimezone(tz=tz)
        self.logger.info(f"Fetching data at {datetime_now}")

        response = requests.get(self.url, timeout=30)
        if response.status_code == requests.codes.OK:
            data = response.json()["data"]["stations"]
            return data
        else:
            raise requests.exceptions.HTTPError(
                f"Request failed with status code: {response.status_code}"
            )


class IVelibRawSaver(abc.ABC):
    """Interface for Velib raw data saver."""

    def __init__(self) -> None:
        """Initialize the Velib raw data saver."""
        self.filename = self._get_filename()

        self.logger = logging.getLogger(__class__.__name__)

    @staticmethod
    def _get_filename() -> str:
        """Get the filename for the file where the data will be saved."""
        tz = pytz.timezone("Europe/Paris")
        datetime_now = datetime.now().astimezone(tz=tz)
        formatted_datetime = datetime_now.strftime("%Y%m%d-%H%M%S")
        return f"velib_availability_real_time_{formatted_datetime}.json"

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
        super().__init__()
        self.save_folder = Path(save_folder)
        self.filepath = self.save_folder / self.filename

    def save(self, data: list) -> None:
        """Save data to a local file."""
        self.logger.info(f"Saving fetched data to file {self.filepath}")
        with open(self.filepath, "w") as file:
            json.dump(data, file)


class S3VelibRawSaver(IVelibRawSaver):
    """Velib raw data saver to S3."""

    def __init__(self) -> None:
        """Initialize the Velib raw data saver to S3."""
        super().__init__()

    def save(self, data: list) -> None:
        """Save the data as a JSON file in an S3 bucket.

        Parameters
        ----------
        data : list
            List of information collected from the Velib API related to the
            availability of spots in Velib stations
        """
        s3_aws_config = S3AWSConfig()
        s3 = boto3.client(
            "s3",
            aws_access_key_id=s3_aws_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=s3_aws_config.AWS_SECRET_ACCESS_KEY,
            region_name=s3_aws_config.REGION_NAME,
        )
        s3.put_object(
            Body=json.dumps(data),
            Bucket=s3_aws_config.VELIB_RAW_BUCKET,
            Key=self.filename,
        )
        self.logger.info(f"Data saved in {self.filename}")


@click.command()
@click.argument("save-folder", type=click.Path(exists=True, file_okay=False))
def fetch_and_save_raw_data(save_folder: str) -> None:
    """Fetch data from the Velib API and save it to a file.

    Parameters
    ----------
    save_folder : str
        Path to the folder where the fetched data will be saved
    """
    data = VelibRawExtractor(API_URL).extract()
    LocalVelibRawSaver(save_folder).save(data)

    click.echo("Fetching and saving data were successful")


@click.command()
def fetch_raw_data_to_s3() -> None:
    """Fetch data from the Velib API and save it to a file.

    Parameters
    ----------
    save_folder : str
        Path to the folder where the fetched data will be saved
    """
    data = VelibRawExtractor(API_URL).extract()
    S3VelibRawSaver().save(data)

    click.echo("Fetching and saving data were successful")
