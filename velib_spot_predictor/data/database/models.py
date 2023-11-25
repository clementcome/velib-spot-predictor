"""Database models for the Velib Spot Predictor."""
from datetime import datetime
from typing import List

from geoalchemy2 import Geometry
from shapely.geometry import Polygon
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for database models."""

    pass


class Station(Base):
    """Station information."""

    __tablename__ = "station_information"
    station_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    capacity: Mapped[int]
    lat: Mapped[float]
    lon: Mapped[float]
    geometry: Mapped[Polygon] = mapped_column(Geometry("POLYGON"))

    status: Mapped[List["Status"]] = relationship(
        "Status",
        backref="station_information",
        order_by="desc(Status.status_datetime)",
    )

    def __repr__(self) -> str:
        """Representation of a station."""
        return f"Station(id={self.station_id!r}, name={self.name!r})"


# class CatchmentArea:
#     """Catchment area of a station."""

#     station_id: Mapped[int] = mapped_column(
#         BigInteger(),
#         ForeignKey("station_information.station_id"),
#         primary_key=True,
#         index=True,
#     )
#     geometry: Mapped[Polygon] = mapped_column(Geometry("POLYGON"))

#     def __repr__(self) -> str:
#         """Representation of a catchment area."""
#         return f"CatchmentArea(station_id={self.station_id!r})"


class Status(Base):
    """Station status."""

    __tablename__ = "station_status"
    station_id: Mapped[int] = mapped_column(
        BigInteger(),
        ForeignKey("station_information.station_id"),
        primary_key=True,
        index=True,
    )
    status_datetime: Mapped[datetime] = mapped_column(
        name="datetime", primary_key=True, index=True
    )
    num_bikes_available: Mapped[int]
    num_bikes_available_types_mechanical: Mapped[int]
    num_bikes_available_types_ebike: Mapped[int]
    num_docks_available: Mapped[int]
    is_installed: Mapped[bool]
    is_returning: Mapped[bool]
    is_renting: Mapped[bool]

    def __repr__(self) -> str:
        """Representation of a station status."""
        return (
            f"Status(station_id={self.station_id!r},"
            f" datetime={self.status_datetime})"
        )


class Arrondissement(Base):
    """Arrondissement information."""

    __tablename__ = "arrondissement"
    c_ar: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    l_ar: Mapped[str] = mapped_column(String(30))
    geometry: Mapped[Polygon] = mapped_column(Geometry("POLYGON"))

    def __repr__(self) -> str:
        """Representation of an arrondissement."""
        return f"Arrondissement(id={self.c_ar!r}, name={self.l_ar!r})"
