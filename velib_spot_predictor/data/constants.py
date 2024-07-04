"""Constants used in the data module."""

from enum import Enum, unique

import pytz

API_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
DATETIME_FORMAT = "%Y%m%d-%H%M%S"
TIMEZONE = pytz.timezone("Europe/Paris")


@unique
class ValueColumns(str, Enum):
    """Columns containing the values of interest."""

    AVAILABLE_BIKES = "num_bikes_available"
    AVAILABLE_MECHANICAL = "num_bikes_available_types_mechanical"
    AVAILABLE_EBIKES = "num_bikes_available_types_ebike"
    AVAILABLE_DOCKS = "num_docks_available"
