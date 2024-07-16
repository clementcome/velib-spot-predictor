"""Database routes in the API."""

from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from velib_spot_predictor.api.database.models import (
    Station,
    StatusDatetimeOutput,
    StatusStationOutput,
)
from velib_spot_predictor.data.constants import ValueColumns
from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.database.models import Station as StationTable
from velib_spot_predictor.data.database.models import Status as StatusTable

router = APIRouter(prefix="/data")


@router.get("/stations")
def get_stations() -> List[Station]:
    """Get all stations."""
    with DatabaseSession() as session:
        stations = session.scalars(select(StationTable)).all()
    return stations


@router.get("/status/station/{station_id}")
def get_station_status(
    station_id: int,
    end_datetime: Annotated[datetime, Query(default_factory=datetime.now)],
    start_datetime: Optional[datetime] = None,
    value: ValueColumns = ValueColumns.AVAILABLE_BIKES,
) -> StatusStationOutput:
    """Get the status of a station between two datetimes."""
    if start_datetime is None:
        start_datetime = end_datetime - timedelta(minutes=15)
    with DatabaseSession() as session:
        station_status = session.execute(
            select(StatusTable.status_datetime, getattr(StatusTable, value))
            .where(
                StatusTable.station_id == station_id,
                StatusTable.status_datetime >= start_datetime,
                StatusTable.status_datetime <= end_datetime,
            )
            .order_by(StatusTable.status_datetime)
        ).all()

    output = StatusStationOutput(
        station_id=station_id,
        value=value,
        datetime=[datetime_ for datetime_, _ in station_status],
        values=[value_ for _, value_ in station_status],
    )
    return output


def get_latest_datetime() -> datetime:
    """Get the latest datetime in the database."""
    with DatabaseSession() as session:
        latest_datetime = session.query(
            func.max(StatusTable.status_datetime)
        ).scalar()
    return latest_datetime


@router.get("/status/datetime")
def get_datetime_status(
    status_datetime: Annotated[
        datetime, Query(default_factory=get_latest_datetime)
    ],
    value: ValueColumns = ValueColumns.AVAILABLE_BIKES,
) -> StatusDatetimeOutput:
    """Get every station status at a given datetime."""
    with DatabaseSession() as session:
        datetime_status = session.execute(
            select(StatusTable.station_id, getattr(StatusTable, value)).where(
                StatusTable.status_datetime >= status_datetime,
                StatusTable.status_datetime
                <= status_datetime + timedelta(minutes=1),
            )
        ).all()

    output = StatusDatetimeOutput(
        status_datetime=status_datetime,
        value=value,
        station_id=[station_id for station_id, _ in datetime_status],
        values=[value_ for _, value_ in datetime_status],
    )
    return output
