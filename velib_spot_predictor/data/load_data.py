"""Loading data submodule."""
import json
from pathlib import Path

import pandas as pd


def load_prepared(path: Path) -> pd.DataFrame:
    """Load prepared data from a file.

    Parameters
    ----------
    path : Path
        Path to the file containing the raw data

    Returns
    -------
    pd.DataFrame
        Raw data
    """
    data = pd.read_pickle(path)
    data = data.sort_values(by=["datetime", "station_id"])
    return data


def load_station_information(path: Path) -> pd.DataFrame:
    """Load station information from a file.

    Parameters
    ----------
    path : Path
        Path to the file containing the station information

    Returns
    -------
    pd.DataFrame
        Station information
    """
    with open(path, "r") as f:
        station_information_raw = json.load(f)
    station_information = pd.DataFrame.from_records(
        station_information_raw["data"]["stations"]
    )

    return station_information
