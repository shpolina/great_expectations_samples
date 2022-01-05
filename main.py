import boto3
from uuid import uuid4
from src.ge_runner import GeRunner

session = boto3.Session(profile_name="mfa", region_name="us-east-1")
credentials = session.client("sts").assume_role(
    RoleArn="", 
    RoleSessionName=str(uuid4())).get("Credentials")
        

runner = GeRunner(
    run_mode="local", 
    connection_str="", 
    aws_access_key=credentials.get("AccessKeyId"),
    aws_secret_key=credentials.get("SecretAccessKey"),
    aws_token=credentials.get("SessionToken"),
    region="us-east-1")

tables_to_validate = [
    {
        "table": "table",
        "schema": "schema",
        "suite" : "test_suite_1"
    },
]

runner.validate_tables(tables_to_validate=tables_to_validate)