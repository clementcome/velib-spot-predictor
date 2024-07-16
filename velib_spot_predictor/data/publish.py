"""Module to transform raw data into a clean database."""

import abc
import json
import re
from datetime import datetime
from functools import cached_property
from io import StringIO
from pathlib import Path
from typing import List, Union

import click
import pandas as pd
from loguru import logger
from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    FilePath,
    NewPath,
    field_validator,
)
from sqlalchemy import select
from tqdm import tqdm

from velib_spot_predictor.data.base import (
    IETL,
    IExtractor,
    ILoader,
    ITransformer,
)
from velib_spot_predictor.data.constants import TIMEZONE
from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.database.models import Station
from velib_spot_predictor.data.load_data import load_station_information

## Utils


class JsonToSQLBase:
    """Base functions for data conversion from json to SQL."""

    @staticmethod
    def _flatten_column(column: pd.Series) -> pd.DataFrame:
        """Flatten the column of a dataframe.

        Parameters
        ----------
        column : pd.Series
            Column to flatten


        Returns
        -------
        pd.DataFrame
            Flattened column
        """
        flattened_column = pd.DataFrame()
        n_columns = len(column.iloc[0])
        for i in range(n_columns):
            name = list(column.iloc[0][i].keys())[0]
            column_name = f"{column.name}_{name}"
            flattened_column[column_name] = column.str[i].str[name]

        return flattened_column

    @staticmethod
    def clean_data(data: pd.DataFrame) -> pd.DataFrame:
        """Clean the data.

        Parameters
        ----------
        data : pd.DataFrame
            Data to clean

        Returns
        -------
        pd.DataFrame
            Cleaned data
        """
        column_to_flatten = ["num_bikes_available_types"]
        for column in column_to_flatten:
            flattened_column = JsonToSQLBase._flatten_column(data[column])
            data = pd.concat([data, flattened_column], axis=1)
        data = data.drop(columns=column_to_flatten)
        return data

    @staticmethod
    def extract_datetime_from_filename(filename: str) -> pd.Timestamp:
        """Extract the datetime from the filename.

        Parameters
        ----------
        filename : str
            Filename to extract the datetime from


        Returns
        -------
        pd.Timestamp
            Extracted datetime
        """
        match = re.search(r"(\d{8}-\d{6})", filename)
        if match:
            datetime_str = match.group(0)
            return pd.Timestamp(datetime_str, tz=TIMEZONE).round("min")
        else:
            raise ValueError("Invalid filename format")


## Extractors


class DataFrameExtractor(BaseModel, IExtractor):
    """Simple extractor to extract the data from an input dataframe."""

    data: list
    timestamp: datetime = Field(
        default_factory=lambda: pd.Timestamp.now(tz=TIMEZONE).floor("min")
    )

    @field_validator("timestamp", mode="after")
    @classmethod
    def check_rounding(cls, timestamp: datetime):
        """Check that the timestamp is rounded to the minute."""
        return pd.Timestamp(timestamp, tz=TIMEZONE).floor("min")

    model_config = {
        "arbitrary_types_allowed": True,
    }

    def extract(self) -> pd.DataFrame:
        """Extract the data.

        Returns
        -------
        pd.DataFrame
            Extracted data
        """
        return JsonToSQLBase.clean_data(
            pd.read_json(StringIO(json.dumps(self.data)))
        ).assign(datetime=self.timestamp)


class FolderExtractor(BaseModel, IExtractor):
    """Extract the data from the raw data folder.

    Parameters
    ----------
    folder_raw_data : DirectoryPath
        Folder containing the raw data
    pattern_raw_data : str, optional
        Pattern to match the raw data files, by default "*.json"
    pbar : bool, optional
        Whether to display a progress bar, by default False
    """

    folder_raw_data: DirectoryPath
    pattern_raw_data: str = "*.json"
    pbar: bool = False

    def _extract_one_file(self, filepath: Path) -> pd.DataFrame:
        """Extract the data from one file.

        Parameters
        ----------
        filepath : Path
            Path to the file to extract


        Returns
        -------
        pd.DataFrame
            Extracted data
        """
        return JsonToSQLBase.clean_data(pd.read_json(filepath))

    def extract(self) -> pd.DataFrame:
        """Extract all the data contained in the folder.

        Parameters
        ----------
        pbar : bool, optional
            Whether to display a progress bar, by default False


        Returns
        -------
        pd.DataFrame
            Extracted data
        """
        data_dict = {}
        for filepath in tqdm(
            list(self.folder_raw_data.glob(self.pattern_raw_data)),
            disable=not self.pbar,
        ):
            logger.info(f"Extracting file {filepath}")
            try:
                data_dict[filepath.name] = self._extract_one_file(
                    filepath
                ).assign(
                    datetime=JsonToSQLBase.extract_datetime_from_filename(
                        filepath.name
                    )
                )
            except Exception as e:
                print(f"Error while extracting file {filepath}: {e}")
        if len(data_dict) == 0:
            raise ValueError("No data extracted")
        data = pd.concat(data_dict, axis=0, ignore_index=True)
        return data


## Transformers


class LocalStationInformationTransformer(BaseModel, ITransformer):
    """Transform the data.

    Get the date from the filename.

    Parameters
    ----------
    station_information_path : FilePath
        Path to the file containing the station information


    Attributes
    ----------
    station_information : pd.DataFrame
        Station information
    """

    station_information_path: FilePath

    @cached_property
    def station_information(self) -> pd.DataFrame:
        """Load the station information."""
        station_information = load_station_information(
            self.station_information_path
        )
        return station_information

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform the data.

        Get the date from the filename.

        Parameters
        ----------
        data : pd.DataFrame
            Data to transform

        Returns
        -------
        pd.DataFrame
            Transformed data
        """
        data = data.merge(
            self.station_information[
                ["station_id", "name", "capacity", "lat", "lon"]
            ],
            left_on="station_id",
            right_on="station_id",
            how="left",
        )
        return data


class SQLStationScopeTransformer(BaseModel, ITransformer):
    """Transform the data.

    Get the date from the filename.
    """

    def _get_station_ids(self) -> List[int]:
        """
        Get station ids present in the Station table.

        Returns
        -------
        List[int]
            List of station ids
        """
        stmt = select(Station.station_id)
        with DatabaseSession() as session:
            station_id_list = session.scalars(stmt).all()
        return station_id_list

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Scope the data to the station ids in the database.

        Parameters
        ----------
        data : pd.DataFrame
            Data to transform

        Returns
        -------
        pd.DataFrame
            Transformed data
        """
        station_id_list = self._get_station_ids()
        is_in_station_id_list = data["station_id"].isin(station_id_list)
        if not is_in_station_id_list.all():
            logger.warning(
                "Data contains station_id not in the database: "
                f"{data[~is_in_station_id_list]['station_id'].unique()}"
            )
        data = data[data["station_id"].isin(station_id_list)]
        return data


## Loaders


class FileLoader(BaseModel, ILoader):
    """Load the data into a file.

    Parameters
    ----------
    output_file : Union[FilePath, NewPath]
        Path to the file to save the data
    """

    output_file: Union[FilePath, NewPath]

    def load(self, data: pd.DataFrame) -> None:
        """Load the data into a file.

        Parameters
        ----------
        data : pd.DataFrame
            Data to load
        """
        data.to_pickle(self.output_file)


class SQLLoader(BaseModel, ILoader):
    """Load the data into a SQL database.

    Parameters
    ----------
    table_name : str
        Name of the table to load the data into
    """

    table_name: str

    def load(self, data: pd.DataFrame) -> None:
        """Load the data into a SQL database.

        Parameters
        ----------
        data : pd.DataFrame
            Data to load
        """
        db_session = DatabaseSession()
        with db_session:
            data[
                [
                    "station_id",
                    "datetime",
                    "num_bikes_available",
                    "num_bikes_available_types_mechanical",
                    "num_bikes_available_types_ebike",
                    "num_docks_available",
                    "is_installed",
                    "is_returning",
                    "is_renting",
                ]
            ].to_sql(
                self.table_name,
                db_session.engine,
                if_exists="append",
                index=False,
                chunksize=200_000,
            )


## ETLs


class SQLDataFrameETL(BaseModel, IETL):
    """ETL to convert raw data into a clean database."""

    data: list

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def extractor(self) -> IExtractor:
        """Extractor."""
        return DataFrameExtractor(data=self.data)

    @property
    def transformer(self) -> ITransformer:
        """Transformer."""
        return SQLStationScopeTransformer()

    @property
    def loader(self) -> ILoader:
        """Loader."""
        return SQLLoader(table_name="station_status")


class BaseFolderETL(BaseModel, IETL):
    """ETL to convert raw data into a clean database."""

    folder_raw_data: DirectoryPath
    pattern_raw_data: str = "*.json"
    pbar: bool = False

    @property
    def extractor(self) -> IExtractor:
        """Extractor."""
        return FolderExtractor(
            folder_raw_data=self.folder_raw_data,
            pattern_raw_data=self.pattern_raw_data,
            pbar=self.pbar,
        )

    @property
    @abc.abstractmethod
    def transformer(self) -> ITransformer:
        """Transformer."""

    @property
    @abc.abstractmethod
    def loader(self) -> ILoader:
        """Loader."""


class FolderToLocalETL(BaseFolderETL):
    """ETL to convert clean raw data and save as local file."""

    station_information_path: FilePath
    output_file: Union[FilePath, NewPath]

    @property
    def transformer(self) -> LocalStationInformationTransformer:
        """Transformer."""
        return LocalStationInformationTransformer(
            station_information_path=self.station_information_path
        )

    @property
    def loader(self) -> FileLoader:
        """Loader."""
        return FileLoader(output_file=self.output_file)


class FolderToSQLETL(BaseFolderETL):
    """ETL to convert clean raw data and push to a database."""

    @property
    def transformer(self) -> SQLStationScopeTransformer:
        """Transformer."""
        return SQLStationScopeTransformer()

    @property
    def loader(self) -> SQLLoader:
        """Loader."""
        return SQLLoader(table_name="station_status")


## CLI


@click.command()
@click.argument("folder_raw_data", type=click.Path(exists=True))
@click.argument("station_information_path", type=click.Path(exists=True))
@click.argument("output_folder", type=click.Path(exists=True))
def conversion_interface(
    folder_raw_data, station_information_path, output_folder
):
    """Convert raw data into a clean database.

    Parameters
    ----------
    folder_raw_data : str
        Folder containing the raw data
    station_information_path : str
        Path to the file containing the station information
    output_folder : str
        Folder where to save the clean database
    """
    # Convert the input arguments to Path objects
    folder_raw_data = Path(folder_raw_data)
    station_information_path = Path(station_information_path)
    output_folder = Path(output_folder)
    # Detect the different dates available in the folder
    filename_list = [
        filepath.name for filepath in folder_raw_data.glob("*.json")
    ]
    datetime_list = [
        filename.split("_")[-1].split(".")[0]
        for filename in filename_list
        if filename.startswith("velib_availability_real_time")
    ]
    date_set = sorted(
        list(
            set(
                [
                    datetime.strptime(date, "%Y%m%d-%H%M%S").date()
                    for date in datetime_list
                ]
            )
        )
    )
    # Show the user the dates already converted in output_folder
    click.echo("Dates already converted:")
    for filepath in sorted(list(output_folder.glob("*.pkl"))):
        click.echo(filepath.name)
    # Ask the user to select the dates to convert using click prompts
    click.echo("Select the dates to convert:")
    dates_to_convert = []
    for _i, date in enumerate(date_set):
        if click.confirm(f"Convert {date} ?"):
            dates_to_convert.append(date)
    for date in dates_to_convert:
        data_conversion_etl = FolderToLocalETL(
            folder_raw_data=folder_raw_data,
            pattern_raw_data=f"*{date:%Y%m%d}*.json",
            station_information_path=station_information_path,
            output_file=output_folder / f"data_{date:%Y%m%d}.pkl",
            pbar=True,
        )
        data_conversion_etl.run()
