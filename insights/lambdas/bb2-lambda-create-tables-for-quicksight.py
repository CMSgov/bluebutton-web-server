import boto3
import re
import time

"""
Summary:

This function will run an Athena SQL query that updates a table
from a view.

This is to be run on a schedule nightly or weekly. It creates an intermediate table
to be used by a DataSet to improve performance in QuickSight.

Pass in the target BASENAME for the intended table and view to use.

For example, BASENAME="global_state_per_app" and ENV="impl" will run the
folowing query in Athena:

   INSERT INTO bb2.impl_global_state_per_app AS SELECT * FROM bb2.vw_impl_global_state_per_app

Lambda function inputs:

{
  "REGION": "<AWS region>",
  "WORKGROUP": "bb2",
  "DATABASE": "bb2",
  "ENV": "<prod/impl/test>"
  "BASENAME": "<basename of view/table>" Ex: "global_state"
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
        "basename": event["BASENAME"],
    }

    # Create table
    params["query"] = (
        "INSERT INTO "
        + event["DATABASE"]
        + "."
        + event["ENV"]
        + "_"
        + event["BASENAME"]
        + " SELECT * FROM "
        + event["DATABASE"]
        + ".vw_"
        + event["ENV"]
        + "_"
        + event["BASENAME"]
    )

    update_output_filename = athena_to_s3_complete(session, params, 300)

    return {
        "STATUS": "SUCCESS",
        "UPDATE_OUTPUT_FILENAME": update_output_filename,
    }
