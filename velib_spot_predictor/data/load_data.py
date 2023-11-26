"""Loading data submodule."""
import json
from pathlib import Path

import pandas as pd
import sqlalchemy


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


def save_station_information_to_sql(
    station_information: pd.DataFrame, engine: sqlalchemy.engine.Engine
):
    """Save station information to a SQL database.

    Parameters
    ----------
    station_information : pd.DataFrame
        Station information
    engine : sqlalchemy.engine.Engine
        SQLAlchemy engine

    Examples
    --------
    >>> from velib_spot_predictor.data.database.context import DatabaseSession
    >>> from velib_spot_predictor.data.load_data import (
    ...     load_station_information, save_station_information_to_sql
    ... )

    >>> station_information = load_station_information(
    ...     "data/raw/station_information.json"
    ...     )

    >>> db_session = DatabaseSession()
    >>> with db_session as session:
    ...     save_station_information_to_sql(
    ...         station_information, db_session.engine
    ...     )
    """
    station_information[
        ["station_id", "name", "lat", "lon", "capacity"]
    ].to_sql(
        "station_information",
        engine,
        if_exists="append",
        index=False,
    )
