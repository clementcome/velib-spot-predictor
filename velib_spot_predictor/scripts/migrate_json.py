"""Migrate JSON files from one bucket to another."""

import json
import re
import sys
from datetime import datetime
from typing import cast

import click
from loguru import logger
from tqdm import tqdm

from velib_spot_predictor.data.fetch import S3VelibRawSaver
from velib_spot_predictor.data.publish import SQLDataFrameETL
from velib_spot_predictor.environment import DBConfig, S3AWSConfig

date_pattern = re.compile(
    r"velib_availability_real_time_([0-9]{8}-[0-9]{6})\.json"
)


@click.command()
@click.option(
    "-i",
    "--input-bucket",
    required=True,
    help="Bucket where the JSON files are stored",
)
@click.option(
    "-p",
    "--file-pattern",
    default=".*",
    help="Pattern of the files to migrate",
)
def migrate_json(input_bucket: str, file_pattern: str):
    """Migrate JSON files from one bucket to another."""
    logger.remove()
    logger.add(sys.stdout)

    config = S3AWSConfig()
    s3_client = config.get_client()
    paginator = s3_client.get_paginator("list_objects")
    page_iterator = paginator.paginate(
        Bucket=input_bucket, Prefix=file_pattern
    )
    logger.info(f"Listing files in bucket {input_bucket}")
    n_objects = 0
    for page in page_iterator:
        n_objects += len(page["Contents"])
    logger.info(f"Found {n_objects} files")

    logger.info(f"Migrating files to bucket {config.VELIB_RAW_BUCKET}")
    db_config = DBConfig()
    db_config.test_connection()
    logger.info(f"Publishing data to the database {db_config.NAME}")
    pbar = tqdm(total=n_objects, desc="Migrating files", unit="file")
    for page in page_iterator:
        for obj in page["Contents"]:
            try:
                pattern_match = date_pattern.match(obj["Key"])
                # Check if the timestamp was extracted
                if not pattern_match:
                    raise ValueError(
                        f"Could not extract timestamp from {obj['Key']}"
                    )
                timestamp_str = cast(
                    re.Match[str], date_pattern.match(obj["Key"])
                ).group(1)
                timestamp_value = datetime.strptime(
                    timestamp_str, "%Y%m%d-%H%M%S"
                )
                # Check if there is already a file in the same minute in the
                # destination bucket
                if "Contents" in s3_client.list_objects(
                    Bucket=config.VELIB_RAW_BUCKET,
                    Prefix=f"{timestamp_value:%Y/%m/%d/%H}/"
                    f"velib_availability_real_time_{timestamp_value:%Y%m%d-%H%M}",
                ):
                    logger.warning(
                        f"File {obj['Key']} already exists in the destination"
                        " bucket"
                    )
                    continue
                data = json.loads(
                    s3_client.get_object(Bucket=input_bucket, Key=obj["Key"])[
                        "Body"
                    ].read()
                )
                S3VelibRawSaver(timestamp_value).save(data)
                SQLDataFrameETL(data=data).run()
            except Exception as e:
                logger.error(f"Error migrating file {obj['Key']}: {e}")
            finally:
                pbar.update(1)
    pbar.close()
    logger.info("Migration complete")
