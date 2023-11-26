import datetime
import json
from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from velib_spot_predictor.data.convert_data import (
    DataConversionETL,
    DataConversionExtractor,
    DataConversionFileLoader,
    DataConversionLocalTransformer,
)


class TestDataConversionExtractor:
    @pytest.fixture
    def mock_folder_raw_data(self, tmp_path: Path):
        folder_raw_data = tmp_path / "raw_data"
        folder_raw_data.mkdir()
        return folder_raw_data

    @pytest.fixture
    def extractor(self, mock_folder_raw_data: Path):
        return DataConversionExtractor(
            folder_raw_data=mock_folder_raw_data, pattern_raw_data="*.json"
        )

    def test_flatten_column(self, extractor: DataConversionExtractor):
        column_to_flatten = pd.Series(
            [
                [{"mechanical": 1}, {"ebike": 2}],
                [{"mechanical": 3}, {"ebike": 4}],
                [{"mechanical": 5}, {"ebike": 6}],
            ],
            name="num_bikes",
            index=[7, 8, 9],
        )
        actual_output = extractor._flatten_column(column_to_flatten)
        expected_output = pd.DataFrame.from_records(
            [
                [1, 2],
                [3, 4],
                [5, 6],
            ],
            columns=["num_bikes_mechanical", "num_bikes_ebike"],
            index=[7, 8, 9],
        )
        pd.testing.assert_frame_equal(actual_output, expected_output)

    def test_extract_one_file(self, tmpdir):
        pass

    def test_extract(self, tmpdir, mocker: MockerFixture):
        date = datetime.datetime.now()
        folder_raw_data = tmpdir.mkdir("raw_data")
        folder_raw_data.join(
            f"velib_availability_real_time_{date:%Y%m%d-%H%M}01.json"
        ).write("")
        folder_raw_data.join(
            f"velib_availability_real_time_{date:%Y%m%d-%H%M}02.json"
        ).write("")
        mock_extract_one_file = mocker.patch.object(
            DataConversionExtractor,
            "_extract_one_file",
            return_value=pd.DataFrame(),
        )
        extractor = DataConversionExtractor(
            folder_raw_data=Path(folder_raw_data), pattern_raw_data="*.json"
        )
        df = extractor.extract()
        assert mock_extract_one_file.call_count == 2
