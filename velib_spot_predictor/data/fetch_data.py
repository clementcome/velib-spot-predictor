import json
from datetime import datetime
from pathlib import Path

import click
import pytz
import requests

api_url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json"


def fetch_data(url):
    response = requests.get(url, timeout=30)
    if response.status_code == requests.codes.OK:
        data = response.json()["data"]["stations"]
        return data
    else:
        raise Exception(f"Response status code was: {response.status_code}")


@click.command()
@click.argument("save-folder", type=click.Path(exists=True, file_okay=False))
def fetch_and_save_raw_data(save_folder: str) -> None:
    tz = pytz.timezone("Europe/Paris")
    datetime_now = datetime.now().astimezone(tz=tz)
    formatted_datetime = datetime_now.strftime("%Y%m%d-%H%M%S")

    click.echo(f"Fetching data at {datetime_now}")
    data = fetch_data(api_url)

    filename = f"velib_availability_real_time_{formatted_datetime}.json"
    filepath = Path(save_folder) / filename
    click.echo(f"Saving fetched data to file {filepath}")
    with open(filepath, "w") as file:
        json.dump(data, file)

    click.echo("Fetching and saving data were successful")
