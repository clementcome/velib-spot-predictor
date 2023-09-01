"""Loading data submodule."""
from pathlib import Path

import pandas as pd
import pytz


def load_raw(path: Path) -> pd.DataFrame:
    """Load raw data from a file.

    Parameters
    ----------
    path : Path
        Path to the file containing the raw data

    Returns
    -------
    pd.DataFrame
        Raw data
    """
    data = pd.read_csv(path, sep=";")
    data["Actualisation de la donnée"] = pd.to_datetime(
        data["Actualisation de la donnée"], utc=True
    )
    tz = pytz.timezone("Europe/Paris")
    data["Actualisation de la donnée"] = data[
        "Actualisation de la donnée"
    ].dt.tz_convert(tz)
    data["Heure"] = (
        data["Actualisation de la donnée"].dt.hour
        + data["Actualisation de la donnée"].dt.minute / 60
    )
    return data
