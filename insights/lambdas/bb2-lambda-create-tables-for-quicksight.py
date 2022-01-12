import boto3
import re
import time

"""
Lambda function inputs:

{
  "REGION": "<AWS region>",
  "WORKGROUP": "bb2",
  "DATABASE": "bb2",
  "ENV": "<prod/impl/test>"
}
"""


def athena_query(client, params):
    # NOTE: Output files will show up in the location configured for the workgroup.
    response = client.start_query_execution(
        QueryString=params["query"],
        QueryExecutionContext={"Database": params["database"]},
        WorkGroup=params["workgroup"],
    )

    return response


def athena_to_s3_complete(session, params, max_execution=60):
    client = session.client("athena", region_name=params["region"])
    execution = athena_query(client, params)
    execution_id = execution["QueryExecutionId"]
    state = "RUNNING"

    while max_execution > 0 and state in ["RUNNING", "QUEUED"]:
        max_execution = max_execution - 1
        response = client.get_query_execution(QueryExecutionId=execution_id)

        if (
            "QueryExecution" in response
            and "Status" in response["QueryExecution"]
            and "State" in response["QueryExecution"]["Status"]
        ):
            state = response["QueryExecution"]["Status"]["State"]
            if state == "FAILED":
                return False
            elif state == "SUCCEEDED":
                s3_path = response["QueryExecution"]["ResultConfiguration"][
                    "OutputLocation"
                ]
                filename = re.findall(r".*\/(.*)", s3_path)[0]
                return filename

        time.sleep(1)

    return False


def lambda_handler(event, context):

    session = boto3.Session()

    params = {
        "region": event["REGION"],
        "workgroup": event["WORKGROUP"],
        "database": event["DATABASE"],
    }

    # Drop table
    params["query"] = (
        "DROP TABLE IF EXISTS "
        + event["DATABASE"]
        + "."
        + event["ENV"]
        + "_global_state"
    )

    drop_output_filename = athena_to_s3_complete(session, params)

    # Create table
    params["query"] = (
        "CREATE TABLE IF NOT EXISTS "
        + event["DATABASE"]
        + "."
        + event["ENV"]
        + "_global_state AS SELECT * FROM "
        + event["DATABASE"]
        + ".vw_"
        + event["ENV"]
        + "_global_state"
    )

    create_output_filename = athena_to_s3_complete(session, params, 300)

    return {
        "STATUS": "SUCCESS",
        "DROP_OUTPUT_FILENAME": drop_output_filename,
        "CREATE_OUTPUT_FILENAME": create_output_filename,
    }

    return
