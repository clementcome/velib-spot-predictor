from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from velib_spot_predictor.data.geo import (
    CatchmentAreaBuilderColumns,
    CatchmentAreaBuilderGeometry,
    ICatchmentAreaBuilder,
)


@pytest.fixture
def mock_points_array():
    return np.array([[0, 0], [0, 2], [2, 2], [2, 0], [1, 1]])


class TestICatchmentAreaBuilder:
    class CatchmentAreaBuilder(ICatchmentAreaBuilder):
        def _log_start(self) -> None:
            pass

        def _check_input(self, df: pd.DataFrame) -> None:
            pass

        def _build_points_array(self, df: pd.DataFrame) -> np.ndarray:
            return mock_points_array()

    def test_build_voronoi(self, mock_points_array: np.ndarray):
        catchment_area_builder = self.CatchmentAreaBuilder()
        voronoi_series = catchment_area_builder._build_points_array(
            mock_points_array
        )
