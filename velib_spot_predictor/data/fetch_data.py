"""Fetch data from the Velib API and save it to a file."""
import json
from datetime import datetime
from pathlib import Path

import click
import pytz
import requests

from velib_spot_predictor.data.constants import API_URL


def fetch_data(url: str) -> list:
    """Fetch data from the Velib API.

    Parameters
    ----------
    url : str
        URL of the Velib API

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
    response = requests.get(url, timeout=30)
    if response.status_code == requests.codes.OK:
        data = response.json()["data"]["stations"]
        return data
    else:
        raise requests.exceptions.HTTPError(
            f"Request failed with status code: {response.status_code}"
        )


@click.command()
@click.argument("save-folder", type=click.Path(exists=True, file_okay=False))
def fetch_and_save_raw_data(save_folder: str) -> None:
    """Fetch data from the Velib API and save it to a file.

    Parameters
    ----------
    save_folder : str
        Path to the folder where the fetched data will be saved
    """
    save_folder: Path = Path(save_folder)
    tz = pytz.timezone("Europe/Paris")
    datetime_now = datetime.now().astimezone(tz=tz)
    formatted_datetime = datetime_now.strftime("%Y%m%d-%H%M%S")

    click.echo(f"Fetching data at {datetime_now}")
    data = fetch_data(API_URL)

    filename = f"velib_availability_real_time_{formatted_datetime}.json"
    filepath = save_folder / filename
    click.echo(f"Saving fetched data to file {filepath}")
    with open(filepath, "w") as file:
        json.dump(data, file)

    click.echo("Fetching and saving data were successful")
