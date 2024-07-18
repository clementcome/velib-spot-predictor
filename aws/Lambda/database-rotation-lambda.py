import secrets

import boto3
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "acc/database"
    region_name = "eu-west-3"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager", region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response["SecretString"]

    # Create a new password
    password = secrets.token_urlsafe(16)
    # Update the password of the RDS database user

    # Update the secret with the new password
