import click
import json
import requests
from tqdm import tqdm
from datetime import datetime
from pathlib import Path

# Replace 'YOUR_API_URL' with the actual API endpoint
api_url = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json'
# data = fetch_data(api_url)

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]["stations"]
        return data
    else:
        raise Exception(f"Response status code was: {response.status_code}")


def fetch_data_with_pagination(base_url, limit=10):
    all_data = []

    # Getting the total_count of records with a first request
    response = requests.get(base_url, params={"limit": 0})
    total_count = response.json().get("total_count")
    if total_count is None:
        raise ValueError("Could not fetch the total count of records.")

    n_iter = total_count // limit + 1

    for i in tqdm(range(n_iter)):
        offset = i*limit
        # Construct the query parameters
        params = {
            'limit': limit,
            'offset': offset
        }

        # Make the API request
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            if not data:
                print("No data received")
                break  # No more data to fetch
            try:
                results = data["results"]
                all_data.extend(results)  # Append current chunk to all_data
            except Exception as e:
                raise e
        else:
            print(f"Request failed with status code: {response.status_code}")
            break

    return all_data


@click.command()
@click.argument("save-folder", type=click.Path(exists=True, file_okay=False))
def fetch_and_save_raw_data(save_folder: str) -> None:
    formatted_datetime = datetime.now().strftime("%Y%m%d-%H%M%S")

    click.echo(f"Fetching data at {datetime.now()}")
    data = fetch_data(api_url)

    filename = f"velib_availability_real_time_{formatted_datetime}.json"
    filepath = Path(save_folder) / filename
    click.echo(f"Saving fetched data to file {filepath}")
    with open(filepath, "w") as file:
        json.dump(data, file)
    
    click.echo("Fetching and saving data were successful")
