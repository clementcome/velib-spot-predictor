import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture
from time_machine import travel
from velib_spot_predictor.data.publish import (
    DataFrameExtractor,
    FileLoader,
    FolderExtractor,
    JsonToSQLBase,
    LocalStationInformationTransformer,
    SQLLoader,
    SQLStationScopeTransformer,
)

from tests.data.conftest import TestDatabaseInteraction


class TestJsonToSQLBase:
    def test_flatten_column(self):
        column_to_flatten = pd.Series(
            [
                [{"mechanical": 1}, {"ebike": 2}],
                [{"mechanical": 3}, {"ebike": 4}],
                [{"mechanical": 5}, {"ebike": 6}],
            ],
            name="num_bikes",
            index=[7, 8, 9],
        )
        actual_output = JsonToSQLBase._flatten_column(column_to_flatten)
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

    def test_clean_data(self):
        data = pd.DataFrame(
            {
                "num_bikes_available_types": [
                    [{"mechanical": 1}, {"ebike": 2}],
                    [{"mechanical": 3}, {"ebike": 4}],
                    [{"mechanical": 5}, {"ebike": 6}],
                ],
                "other_column": [10, 20, 30],
            },
            index=[7, 8, 9],
        )
        actual_output = JsonToSQLBase.clean_data(data)
        expected_output = pd.DataFrame(
            {
                "other_column": [10, 20, 30],
                "num_bikes_available_types_mechanical": [1, 3, 5],
                "num_bikes_available_types_ebike": [2, 4, 6],
            },
            index=[7, 8, 9],
        )
        pd.testing.assert_frame_equal(actual_output, expected_output)

    def test_extract_datetime_from_filename(self):
        # Given
        filename = "velib_availability_real_time_20210101-120010.json"
        # When
        actual = JsonToSQLBase.extract_datetime_from_filename(filename)
        # Then
        expected = datetime(2021, 1, 1, 12, 0)
        assert actual == expected
        expected_pandas = pd.Timestamp("2021-01-01 12:00")
        assert actual == expected_pandas

    def test_extract_datetime_from_filename_should_raise(self):
        # Given
        filename = "velib_2021.json"
        with pytest.raises(ValueError, match="Invalid filename format"):
            # When
            JsonToSQLBase.extract_datetime_from_filename(filename)


class TestDataFrameExtractor:
    @pytest.fixture
    def fake_raw_data(self):
        return [
            {
                "station_id": 1,
                "num_bikes_available": 2,
                "num_bikes_available_types": [
                    {"mechanical": 1},
                    {"ebike": 1},
                ],
            }
        ]

    @travel("2021-01-01 12:00:10")
    def test_init(self, fake_raw_data):
        # When
        extractor = DataFrameExtractor(data=fake_raw_data)
        # Then
        assert extractor.data == fake_raw_data
        assert extractor.timestamp == datetime(2021, 1, 1, 12, 0, 0)

    def test_init_with_timestamp(self, fake_raw_data):
        timestamp = datetime(2021, 1, 1, 12, 1, 10)
        # When
        extractor = DataFrameExtractor(data=fake_raw_data, timestamp=timestamp)
        # Then
        assert extractor.data == fake_raw_data
        assert extractor.timestamp == datetime(2021, 1, 1, 12, 1, 0)  # Rounded

    @travel("2021-01-01 12:00:10")
    def test_extract(self, fake_raw_data):
        # Given
        extractor = DataFrameExtractor(data=fake_raw_data)
        # When
        df = extractor.extract()
        # Then
        expected_df = pd.DataFrame(
            {
                "station_id": [1],
                "num_bikes_available": [2],
                "num_bikes_available_types_mechanical": [1],
                "num_bikes_available_types_ebike": [1],
                "datetime": [pd.Timestamp("2021-01-01 12:00")],
            }
        )
        pd.testing.assert_frame_equal(
            df,
            expected_df.astype({"datetime": "datetime64[us]"}),
            check_datetimelike_compat=True,
        )


class TestFolderExtractor:
    @pytest.fixture
    def extractor(self, mocker: MockerFixture):
        path_raw_data = Path("raw_data")

        def mock_is_dir(path):
            if path == path_raw_data:
                return True
            return Path.is_dir(path)

        mocker.patch.object(Path, "is_dir", side_effect=mock_is_dir, autospec=True)
        return FolderExtractor(folder_raw_data=path_raw_data, pattern_raw_data="*.json")

    @pytest.fixture
    def fake_dataframe(self):
        return pd.DataFrame(
            [
                {
                    "station_id": 1,
                    "num_bikes_available": 2,
                    "num_bikes_available_types": [
                        {"mechanical": 1},
                        {"ebike": 1},
                    ],
                }
            ]
        )

    def test_extract_one_file(
        self, mocker: MockerFixture, fake_dataframe, extractor: FolderExtractor
    ):
        # Given
        filepath = f"velib_availability_real_time_{datetime.now():%Y%m%d-%H%M}01.json"
        mock_read_json = mocker.patch.object(
            pd, "read_json", return_value=fake_dataframe
        )

        # When
        actual_df = extractor._extract_one_file(filepath)

        # Then
        expected_df = pd.DataFrame(
            {
                "station_id": [1],
                "num_bikes_available": [2],
                "num_bikes_available_types_mechanical": [1],
                "num_bikes_available_types_ebike": [1],
            }
        )
        mock_read_json.assert_called_once_with(filepath)
        pd.testing.assert_frame_equal(actual_df, expected_df)

    def test_extract(self, mocker: MockerFixture, extractor: FolderExtractor):
        mock_glob = mocker.patch.object(
            Path,
            "glob",
            return_value=[
                Path(
                    f"velib_availability_real_time_{datetime.now():%Y%m%d-%H%M}01.json"
                ),
                Path(
                    f"velib_availability_real_time_{datetime.now():%Y%m%d-%H%M}02.json"
                ),
            ],
        )

        mock_extract_one_file = mocker.patch.object(
            FolderExtractor,
            "_extract_one_file",
            return_value=pd.DataFrame(),
        )

        extractor.extract()

        mock_glob.assert_called_once()
        assert mock_extract_one_file.call_count == 2

    def test_extract_should_raise(self, mocker: MockerFixture, extractor):
        mock_glob = mocker.patch.object(Path, "glob")

        with pytest.raises(ValueError, match="No data extracted"):
            extractor.extract()


class TestLocalStationInformationTransformer:
    @pytest.fixture
    def transformer(self, mocker: MockerFixture):
        station_information_path = "path/to/station_information.csv"
        mocker.patch(
            "velib_spot_predictor.data.publish.load_station_information",
            return_value=pd.DataFrame(
                {
                    "station_id": [1, 2, 3],
                    "name": ["Station 1", "Station 2", "Station 3"],
                    "capacity": [10, 20, 30],
                    "lat": [1.0, 2.0, 3.0],
                    "lon": [4.0, 5.0, 6.0],
                }
            ),
        )
        mocker.patch.object(Path, "is_file", return_value=True)
        return LocalStationInformationTransformer(
            station_information_path=station_information_path
        )

    def test_transform(self, transformer: LocalStationInformationTransformer):
        # Given
        data = pd.DataFrame(
            {
                "station_id": [1, 2, 3],
                "other_column": [10, 20, 30],
            }
        )
        expected_output = pd.DataFrame(
            {
                "station_id": [1, 2, 3],
                "other_column": [10, 20, 30],
                "name": ["Station 1", "Station 2", "Station 3"],
                "capacity": [10, 20, 30],
                "lat": [1.0, 2.0, 3.0],
                "lon": [4.0, 5.0, 6.0],
            }
        )
        # When
        transformed_data = transformer.transform(data)
        # Then
        pd.testing.assert_frame_equal(transformed_data, expected_output)


class TestSQLStationScopeTransformer(TestDatabaseInteraction):
    def test_get_station_ids(self):
        # When
        station_ids = SQLStationScopeTransformer()._get_station_ids()
        # Then
        assert station_ids == [1, 2]

    def test_transform_should_filter_ids(self, caplog: pytest.LogCaptureFixture):
        # Given
        data = pd.DataFrame.from_records(
            [
                [0, datetime(2023, 12, 10, 12, 0), 5],
                [1, datetime(2023, 12, 10, 12, 0), 5],
            ],
            columns=["station_id", "status_datetime", "num_bikes_available"],
        ).assign(
            num_bikes_available_types_mechanical=2,
            num_bikes_available_types_ebike=3,
            num_docks_available=5,
            is_installed=True,
            is_returning=True,
            is_renting=True,
        )
        with caplog.at_level(logging.WARNING):
            # When
            actual = SQLStationScopeTransformer().transform(data)
        # Then
        assert len(caplog.messages) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "Data contains station_id not in the database: [0]" in caplog.messages[0]
        expected = pd.DataFrame.from_records(
            [
                [1, datetime(2023, 12, 10, 12, 0), 5],
            ],
            columns=["station_id", "status_datetime", "num_bikes_available"],
        ).assign(
            num_bikes_available_types_mechanical=2,
            num_bikes_available_types_ebike=3,
            num_docks_available=5,
            is_installed=True,
            is_returning=True,
            is_renting=True,
        )
        pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)


class TestFileLoader:
    def test_load(self, mocker: MockerFixture):
        mock_to_pickle = mocker.patch.object(pd.DataFrame, "to_pickle")
        mocker.patch.object(Path, "is_file", return_value=True)
        fake_output_path = Path("fake_filepath")
        loader = FileLoader(output_file=fake_output_path)

        loader.load(pd.DataFrame())
        mock_to_pickle.assert_called_once_with(fake_output_path)


class TestSQLLoader(TestDatabaseInteraction):
    def test_load(self, mocker: MockerFixture):
        data_to_load = pd.DataFrame.from_records(
            [
                [1, datetime(2023, 12, 10, 12, 0), 5],
            ],
            columns=["station_id", "datetime", "num_bikes_available"],
        ).assign(
            num_bikes_available_types_mechanical=2,
            num_bikes_available_types_ebike=3,
            num_docks_available=5,
            is_installed=True,
            is_returning=True,
            is_renting=True,
        )
        mock_to_sql = mocker.patch.object(pd.DataFrame, "to_sql")
        fake_table_name = ""
        loader = SQLLoader(table_name=fake_table_name)
        loader.load(data_to_load)

        mock_to_sql.assert_called_once()
