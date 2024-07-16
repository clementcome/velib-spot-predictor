"""Command line interface for the data module."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import pandas as pd
from sqlalchemy import func, select
from tqdm import tqdm

from velib_spot_predictor.data.constants import API_URL
from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.database.models import Status
from velib_spot_predictor.data.fetch import (
    LocalVelibRawSaver,
    S3VelibRawSaver,
    VelibRawExtractor,
)
from velib_spot_predictor.data.load_data import (
    load_station_information,
    save_station_information_to_sql,
)
from velib_spot_predictor.data.publish import FolderToSQLETL, SQLDataFrameETL


@click.command()
@click.option(
    "-s",
    "--save-folder",
    type=click.Path(exists=True, file_okay=False),
    help="Local folder where the data will be saved",
)
@click.option("--s3", is_flag=True, help="Save the data in an S3 bucket")
@click.option("--database", is_flag=True, help="Load the data in the database")
def fetch_data(
    save_folder: Optional[str] = None, s3: bool = False, database: bool = False
) -> None:
    """Fetch data from the Velib API and save it."""
    data = VelibRawExtractor(API_URL).extract()
    click.echo("Data fetched successfully")
    if not any([save_folder, s3, database]):
        click.echo("No save option selected, data will not be saved")
    if save_folder:
        try:
            LocalVelibRawSaver(save_folder).save(data)
            click.echo("Data saved locally")
        except Exception as e:
            click.echo(f"Failed to save data locally: {str(e)}")
    if s3:
        try:
            S3VelibRawSaver().save(data)
            click.echo("Data saved in S3")
        except Exception as e:
            click.echo(f"Failed to save data in S3: {str(e)}")
    if database:
        try:
            SQLDataFrameETL(data=data).run()
            click.echo("Data loaded in the database")
        except Exception as e:
            click.echo(f"Failed to load data in the database: {str(e)}")


@click.command()
@click.argument("station_information_path", type=click.Path(exists=True))
def fill_station_information_table(station_information_path: str):
    """Fill station_information table.

    STATION_INFORMATION_PATH is the path to the file containing the station
    information.
    """
    station_information = load_station_information(
        Path(station_information_path)
    )
    db_session = DatabaseSession()
    with db_session:
        save_station_information_to_sql(station_information, db_session.engine)


def prompt_for_correct_date(
    date_name: str, date_default: Optional[datetime] = None, max_tries: int = 3
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
    """Load the data from FOLDER_RAW_DATA into a SQL database."""
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
        data_conversion_etl = FolderToSQLETL(
            folder_raw_data=folder_raw_data,
            pattern_raw_data=filename,
            pbar=False,
        )
        try:
            data_conversion_etl.run()
        except ValueError as e:
            print(f"Error while converting file {filename}: {e}")
