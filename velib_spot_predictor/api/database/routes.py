"""Database routes in the API."""
from datetime import timedelta
from typing import List

from fastapi import APIRouter
from sqlalchemy import select

from velib_spot_predictor.api.database.models import (
    Station,
    StatusDatetimeInput,
    StatusDatetimeOutput,
    StatusStationInput,
    StatusStationOutput,
)
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


@router.post("/status/station")
def get_station_status(
    status_station_input: StatusStationInput,
) -> StatusStationOutput:
    """Get the status of a station between two datetimes."""
    station_id = status_station_input.station_id
    start_datetime = status_station_input.start_datetime
    end_datetime = status_station_input.end_datetime
    value = status_station_input.value

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


@router.post("/status/datetime")
def get_datetime_status(
    status_datetime_input: StatusDatetimeInput,
) -> StatusDatetimeOutput:
    """Get every station status at a given datetime."""
    status_datetime = status_datetime_input.status_datetime
    value = status_datetime_input.value

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
