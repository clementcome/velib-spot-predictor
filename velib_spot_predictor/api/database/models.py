"""Database models for the API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from velib_spot_predictor.data.constants import ValueColumns


class Station(BaseModel):
    """Station Model."""

    station_id: int
    name: str
    capacity: int
    lat: Optional[float]
    lon: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class StatusStationInput(BaseModel):
    """Input model for getting the status of a station."""

    station_id: int
    start_datetime: datetime
    end_datetime: datetime
    value: ValueColumns

    model_config = ConfigDict(from_attributes=True)


class StatusStationOutput(BaseModel):
    """Output model for getting the status of a station."""

    station_id: int
    value: ValueColumns
    datetime: List[datetime]
    values: List[float]

    model_config = ConfigDict(from_attributes=True)


class StatusDatetimeInput(BaseModel):
    """Input model for getting every station status at a given datetime."""

    status_datetime: datetime
    value: ValueColumns

    model_config = ConfigDict(from_attributes=True)


class StatusDatetimeOutput(BaseModel):
    """Output model for getting every station status at a given datetime."""

    status_datetime: datetime
    value: ValueColumns
    station_id: List[int]
    values: List[float]

    model_config = ConfigDict(from_attributes=True)
