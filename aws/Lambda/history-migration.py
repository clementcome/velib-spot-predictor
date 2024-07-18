import os
import subprocess

from velib_spot_predictor.environment import AWSConfig


def lambda_handler(event, context):
    # Set environment variables based on ENVIRONMENT variable
    secretsmanager = AWSConfig().get_client("secretsmanager")
    if event["ENVIRONMENT"] == "dev":
        bucket = "development-velib"
        secret_id = "dev/database"
        db_name = "development"
    elif event["ENVIRONMENT"] == "acc":
        bucket = "acceptance-velib"
        secret_id = "acc/database"
        db_name = "acceptance"
    elif event["ENVIRONMENT"] == "prod":
        bucket = "production-velib"
        secret_id = "prod/database"
        db_name = "production"
    else:
        raise ValueError(f"Invalid {event['ENVIRONMENT']=} value")

    # Set environment variables
    os.environ["S3_VELIB_RAW_BUCKET"] = bucket
    db_secret = secretsmanager.get_secret_value(SecretId=secret_id)[
        "SecretString"
    ]
    os.environ["DB_NAME"] = db_name
    os.environ["DB_USER"] = db_secret["username"]
    os.environ["DB_PASSWORD"] = db_secret["password"]
    os.environ["DB_HOST"] = db_secret["host"]
    os.environ["DB_PORT"] = db_secret["port"]

    # Get arguments from event
    input_bucket = event["input_bucket"]
    file_pattern = event["file_pattern"]

    subprocess.run(
        ["migrate-json", "-i", input_bucket, "-p", file_pattern],  # noqa: S603, S607
        check=False,
    )

    return {"statusCode": 200, "body": "Completed migration"}
