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

MOCK_POINTS_ARRAY = np.array([[0, 0], [0, 2], [2, 2], [2, 0], [1, 1]])


class TestICatchmentAreaBuilder:
    class CatchmentAreaBuilder(ICatchmentAreaBuilder):
        def _log_start(self) -> None:
            pass

        def _check_input(self, df: pd.DataFrame) -> None:
            pass

        def _build_points_array(self, df: pd.DataFrame) -> np.ndarray:
            return MOCK_POINTS_ARRAY

    def test_build_voronoi(self):
        catchment_area_builder = self.CatchmentAreaBuilder()
        catchment_area_builder._build_points_array(
            MOCK_POINTS_ARRAY
        )
