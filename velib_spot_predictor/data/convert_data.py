"""Module to transform raw data into a clean database."""
import logging
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Union

import click
import pandas as pd
from pydantic import BaseModel, DirectoryPath, FilePath, NewPath
from tqdm import tqdm

from velib_spot_predictor.data.base import (
    IETL,
    IExtractor,
    ILoader,
    ITransformer,
)
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
        data = pd.concat(data_dict, axis=0).reset_index(
            names=["filename", "index"]
        )
        return data


class DataConversionTransformer(BaseModel, ITransformer):
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


class DataConversionETL(BaseModel, IETL):
    """ETL to convert raw data into a clean database."""

    folder_raw_data: DirectoryPath
    pattern_raw_data: str = "*.json"
    station_information_path: FilePath
    output_file: Union[FilePath, NewPath]
    pbar: bool = False

    @property
    def extractor(self) -> DataConversionExtractor:
        """Extractor."""
        return DataConversionExtractor(
            folder_raw_data=self.folder_raw_data,
            pattern_raw_data=self.pattern_raw_data,
            pbar=self.pbar,
        )

    @property
    def transformer(self) -> DataConversionTransformer:
        """Transformer."""
        return DataConversionTransformer(
            station_information_path=self.station_information_path
        )

    @property
    def loader(self) -> DataConversionFileLoader:
        """Loader."""
        return DataConversionFileLoader(output_file=self.output_file)


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
        data_conversion_etl = DataConversionETL(
            folder_raw_data=folder_raw_data,
            pattern_raw_data=f"*{date:%Y%m%d}*.json",
            station_information_path=station_information_path,
            output_file=output_folder / f"data_{date:%Y%m%d}.pkl",
        )
        data = data_conversion_etl.extract(pbar=True)
        data = data_conversion_etl.transform(data)
        data_conversion_etl.load(data)


if __name__ == "__main__":
    conversion_interface()

# if __name__ == "__main__":
#     for day in ["20230905", "20230831", "20230901", "20230902", "20230903"]:
#         data_conversion_etl = DataConversionETL(
#             folder_raw_data="data/raw/automated_fetching",
#             pattern_raw_data=f"*{day}*.json",
#             station_information_path="data/raw/station_information.json",
#             output_file=f"data/interim/data_{day}.pkl",
#         )
#         data = data_conversion_etl.extract(pbar=True)
#         data = data_conversion_etl.transform(data)
#         data_conversion_etl.load(data)
#     print(data.head())
#     print(data.columns)
#     print("Done!")
