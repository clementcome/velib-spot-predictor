"""Module to transform raw data into a clean database."""
import abc
import logging
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Union

import click
import pandas as pd
from pydantic import BaseModel, DirectoryPath, FilePath, NewPath
from sqlalchemy import func, select
from tqdm import tqdm

from velib_spot_predictor.data.base import (
    IETL,
    IExtractor,
    ILoader,
    ITransformer,
)
from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.database.models import Station, Status
from velib_spot_predictor.data.load_data import load_station_information
from velib_spot_predictor.utils import get_one_filepath

logger = logging.getLogger(__name__)


class DataConversionExtractor(BaseModel, IExtractor):
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

    def _find_filepath(self, date: datetime) -> str:
        """Find the filename corresponding to the date.

        Parameters
        ----------
        date : datetime
            Date to find the filename for


        Returns
        -------
        str
            Filename corresponding to the date
        """
        file_pattern = f"velib_availability_real_time_{date:%Y%m%d-%H%M}*.json"
        filepath = get_one_filepath(self.folder_raw_data, file_pattern)
        return filepath

    def _flatten_column(self, column: pd.Series) -> pd.DataFrame:
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
        data = pd.read_json(filepath)
        column_to_flatten = ["num_bikes_available_types"]
        for column in column_to_flatten:
            flattened_column = self._flatten_column(data[column])
            data = pd.concat([data, flattened_column], axis=1)
        data = data.drop(columns=column_to_flatten)
        return data

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
            try:
                data_dict[filepath.name] = self._extract_one_file(filepath)
            except Exception as e:
                print(f"Error while extracting file {filepath}: {e}")
        if len(data_dict) == 0:
            raise ValueError("No data extracted")
        data = pd.concat(data_dict, axis=0).reset_index(
            names=["filename", "index"]
        )
        return data


class DataConversionLocalTransformer(BaseModel, ITransformer):
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
        data["datetime"] = pd.to_datetime(
            data["filename"].str.extract(r"(\d{8}-\d{6})")[0],
            format="%Y%m%d-%H%M%S",
            errors="coerce",
        )
        data = data.drop(columns=["filename", "index"])
        data = data.merge(
            self.station_information[
                ["station_id", "name", "capacity", "lat", "lon"]
            ],
            left_on="station_id",
            right_on="station_id",
            how="left",
        )
        return data


class DataConversionFileLoader(BaseModel, ILoader):
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


class DataConversionSQLTransformer(BaseModel, ITransformer):
    """Transform the data.

    Get the date from the filename.
    """

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
        data["datetime"] = pd.to_datetime(
            data["filename"].str.extract(r"(\d{8}-\d{6})")[0],
            format="%Y%m%d-%H%M%S",
            errors="coerce",
        )
        data = data.drop(columns=["filename", "index"])
        stmt = select(Station.station_id)
        with DatabaseSession() as session:
            station_id_list = session.scalars(stmt).all()
        data = data[data["station_id"].isin(station_id_list)]
        return data


class DataConversionSQLLoader(BaseModel, ILoader):
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


class DataConversionETL(BaseModel, IETL):
    """ETL to convert raw data into a clean database."""

    folder_raw_data: DirectoryPath
    pattern_raw_data: str = "*.json"
    pbar: bool = False

    @property
    def extractor(self) -> IExtractor:
        """Extractor."""
        return DataConversionExtractor(
            folder_raw_data=self.folder_raw_data,
            pattern_raw_data=self.pattern_raw_data,
            pbar=self.pbar,
        )

    @property
    @abc.abstractmethod
    def transformer(self) -> DataConversionLocalTransformer:
        """Transformer."""

    @property
    @abc.abstractmethod
    def loader(self) -> ILoader:
        """Loader."""


class DataConversionLocalETL(DataConversionETL):
    """ETL to convert clean raw data and save as local file."""

    station_information_path: FilePath
    output_file: Union[FilePath, NewPath]

    @property
    def transformer(self) -> DataConversionLocalTransformer:
        """Transformer."""
        return DataConversionLocalTransformer(
            station_information_path=self.station_information_path
        )

    @property
    def loader(self) -> DataConversionFileLoader:
        """Loader."""
        return DataConversionFileLoader(output_file=self.output_file)


class DataConversionSQLETL(DataConversionETL):
    """ETL to convert clean raw data and push to a database."""

    @property
    def transformer(self) -> DataConversionSQLTransformer:
        """Transformer."""
        return DataConversionSQLTransformer()

    @property
    def loader(self) -> DataConversionSQLLoader:
        """Loader."""
        return DataConversionSQLLoader(table_name="station_status")


def prompt_for_correct_date(
    date_name: str, date_default: datetime = None, max_tries: int = 3
) -> datetime:
    """Prompt the user for a date."""
    date_format = "%Y%m%d%H%M"
    n_tries = 0
    while n_tries < max_tries:
        try:
            n_tries += 1
            prompt = (
                f"Enter value for {date_name} date, format should be"
                f" YYYYMMDD(HH(MM)) {n_tries}/{max_tries} tries"
            )
            if date_default is not None:
                prompt += f" (default = {date_default.strftime(date_format)})"
            input_date = click.prompt(prompt, default="", show_default=False)
            if (input_date == "") and (date_default is not None):
                return date_default
            original_input_date_length = len(input_date)
            len_day = 8
            len_hour = 10
            len_minute = 12
            if len(input_date) == len_day:
                input_date += "00"
            if len(input_date) == len_hour:
                input_date += "00"
            if len(input_date) != len_minute:
                raise ValueError(
                    "Length of the input shoud be either 8, 10 or 12"
                    f", found {original_input_date_length}"
                )

            # This raises ValueError when failing
            input_date_converted = datetime.strptime(input_date, date_format)
            break

        except ValueError as e:
            if n_tries < max_tries:
                print(e)
            else:
                print(e)
                raise click.ClickException(
                    "Max number of tries reached"
                ) from None

    return input_date_converted


@click.command()
@click.argument("folder_raw_data", type=click.Path(exists=True))
def load_to_sql(folder_raw_data):
    """Load the data into a SQL database.

    Parameters
    ----------
    folder_raw_data : str
        Folder containing the raw data
    """
    # Convert the input arguments to Path objects
    folder_raw_data = Path(folder_raw_data)
    # Detect the different dates available in the folder
    file_df = pd.DataFrame(
        [
            {
                "filename": filepath.name,
                "datetime": datetime.strptime(
                    filepath.name.split("_")[-1].split(".")[0],
                    "%Y%m%d-%H%M%S",
                ),
            }
            for filepath in folder_raw_data.glob(
                "velib_availability_real_time*.json"
            )
        ]
    )

    def get_last_datetime_in_table():
        stmt = select(func.max(Status.status_datetime))
        with DatabaseSession() as session:
            last_datetime_in_table = session.scalar(stmt)
        if last_datetime_in_table is None:
            last_datetime_in_table = datetime(2020, 1, 1)
        return last_datetime_in_table

    last_datetime_in_table = get_last_datetime_in_table()

    # Show the user the dates already converted in output_folder
    click.echo(f"Dates already converted until {last_datetime_in_table}.")

    # Get the start and end date the user wants to load to the database
    start_date = prompt_for_correct_date("start", last_datetime_in_table)
    end_date = prompt_for_correct_date("end", datetime.now())
    click.echo(
        f"Loading data from {start_date} to {end_date} in sql database."
    )

    files_to_convert = (
        file_df[
            (file_df["datetime"] > start_date)
            & (file_df["datetime"] <= end_date)
        ]["filename"]
        .sort_values()
        .to_list()
    )

    for filename in tqdm(files_to_convert):
        data_conversion_etl = DataConversionSQLETL(
            folder_raw_data=folder_raw_data,
            pattern_raw_data=filename,
            pbar=False,
        )
        try:
            data_conversion_etl.run()
        except ValueError as e:
            print(f"Error while converting file {filename}: {e}")


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
        data_conversion_etl = DataConversionLocalETL(
            folder_raw_data=folder_raw_data,
            pattern_raw_data=f"*{date:%Y%m%d}*.json",
            station_information_path=station_information_path,
            output_file=output_folder / f"data_{date:%Y%m%d}.pkl",
            pbar=True,
        )
        data_conversion_etl.run()


if __name__ == "__main__":
    load_to_sql()
