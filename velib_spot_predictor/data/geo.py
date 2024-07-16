"""Handle geographical operations."""

import abc
import logging
from dataclasses import dataclass
from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


class ICatchmentAreaBuilder(abc.ABC):
    """Build the catchment area of a set of points."""

    def run(
        self,
        df: Union[pd.DataFrame, gpd.GeoDataFrame],
    ) -> gpd.GeoSeries:
        """Build the catchment area of a set of points.

        Parameters
        ----------
        df : Union[pd.DataFrame, gpd.GeoDataFrame]
            The dataframe containing the points.


        Returns
        -------
        gpd.GeoSeries
            The catchment area of the points.
        """
        self._log_start()
        self._check_input(df)
        points_array = self._build_points_array(df)
        voronoi_series = self._build_voronoi(points_array, df.index)
        self._log_end(voronoi_series)
        return voronoi_series

    @abc.abstractmethod
    def _log_start(self) -> None:
        """Log the start of the catchment area building."""

    @abc.abstractmethod
    def _check_input(self, df: Union[pd.DataFrame, gpd.GeoDataFrame]) -> None:
        """Check the input dataframe."""

    @abc.abstractmethod
    def _build_points_array(
        self, df: Union[pd.DataFrame, gpd.GeoDataFrame]
    ) -> np.ndarray:
        """Build the array of points."""

    @staticmethod
    def _build_voronoi(
        points_array: np.ndarray, index: pd.Index
    ) -> gpd.GeoSeries:
        """Build the Voronoi diagram.

        Parameters
        ----------
        points_array : np.ndarray
            The array of points.
        index : pd.Index
            The index of the points.


        Returns
        -------
        gpd.GeoSeries
            The Voronoi diagram.


        Notes
        -----
        The Voronoi diagram is built using the scipy.spatial.Voronoi class.
        """
        vor = Voronoi(points_array)
        polygons = []
        for idx in vor.point_region:
            region = vor.regions[idx]
            if -1 not in region:
                polygons.append(Polygon(vor.vertices[region]))
            else:
                polygons.append(Polygon())
        voronoi_series = gpd.GeoSeries(polygons, index=index)
        return voronoi_series

    @staticmethod
    def _log_end(voronoi_series: gpd.GeoSeries) -> None:
        """Log the end of the catchment area building.

        Parameters
        ----------
        voronoi_series : gpd.GeoSeries
            The Voronoi diagram.


        Notes
        -----
        The number of polygons is computed as the number of non-null
        geometries.
        """
        logger.info(
            f"Voronoi diagram built with"
            f" {(~voronoi_series.geometry.isna()).sum()} polygons."
        )


class CatchmentAreaBuilderGeometry(ICatchmentAreaBuilder):
    """Build the catchment area of a set of points from a geometry column."""

    def _log_start(self) -> None:
        """Log the start of the catchment area building."""
        logger.info("Building catchment area from geometry.")

    def _check_input(self, df: gpd.GeoDataFrame) -> None:
        """Check the input dataframe.

        Parameters
        ----------
        df : gpd.GeoDataFrame
            The input dataframe.


        Raises
        ------
        ValueError
            If the input dataframe does not contain only points.
        """
        is_point = df.geometry.type == "Point"
        if not is_point.all():
            raise ValueError(
                "The input GeoDataFrame must contain only points."
            )

    def _build_points_array(self, df: gpd.GeoDataFrame) -> np.ndarray:
        """Build the array of points.

        Parameters
        ----------
        df : gpd.GeoDataFrame
            The input dataframe.


        Returns
        -------
        np.ndarray
            The array of points.
        """
        return np.array(df.geometry.apply(lambda p: [p.x, p.y]).to_list())


@dataclass
class CatchmentAreaBuilderColumns(ICatchmentAreaBuilder):
    """Build the catchment area from longitude and latitude columns."""

    longitude: str = "longitude"
    latitude: str = "latitude"

    def _log_start(self) -> None:
        """Log the start of the catchment area building."""
        logger.info(
            f"Building catchment area from {self.longitude=} and "
            f"{self.latitude=} columns."
        )

    def _check_input(self, df: gpd.GeoDataFrame) -> None:
        """Check the input dataframe.

        Parameters
        ----------
        df : gpd.GeoDataFrame
            The input dataframe.


        Raises
        ------
        ValueError
            If the input dataframe does not contain the longitude and latitude
            columns.
        """
        # Assert that the input dataframe contains the longitude and latitude
        # columns
        if self.longitude not in df.columns:
            raise ValueError(
                f"The input dataframe must contain a {self.longitude=} column."
            )
        if self.latitude not in df.columns:
            raise ValueError(
                f"The input dataframe must contain a {self.latitude=} column."
            )

    def _build_points_array(self, df: gpd.GeoDataFrame) -> np.ndarray:
        """Build the array of points.

        Parameters
        ----------
        df : gpd.GeoDataFrame
            The input dataframe.


        Returns
        -------
        np.ndarray
            The array of points.
        """
        return df[[self.longitude, self.latitude]].to_numpy()
