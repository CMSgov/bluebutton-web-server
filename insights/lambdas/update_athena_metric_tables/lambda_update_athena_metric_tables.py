import boto3

from utils.utils import (
    get_report_dates_from_target_date,
    update_or_create_metrics_table,
)


"""
Summary:

This lambda supports the updating (or creation) of metric
tables via Athena used for BB2 Insights dashboards in QuickSight.

It does the following:

- Accepts a lambda parameters dictionary in the following format:
    {
      "REGION": "<AWS region>",
      "WORKGROUP": "bb2",
      "DATABASE": "bb2",
      "ENV": "<prod/impl/test>"
      "BASENAME_MAIN": "<basename of main table>" Ex: "global_state"
      "BASENAME_PER_APP": "<basename of per-app table>" Ex: "global_state_per_app"
      "TARGET_DATE": <target report date week> EX: "2022-09-19",
    }

- Computes the report_date, start_date, and end_date based on the TARGET_DATE param.

  - If the TARGET_DATE is blank, the current date will be used for the TARGET_DATE.

- Updates (or creates) the per-applications table for the target report_date,
  ENV and BASENAME_PER_APP params.

- Updates (or creates) the main (top-level) table for the target report_date,
  ENV and BASENAME_MAIN params.

For each of the tables, it does the following:

- Check if the table already exists. Setup to create it, if not.

- Check if an entry for the report_date already exists to prevent duplicate
  entries.

- Execute the relatate SQL from the corresponding template file and
  update (or create) the table with the results.

- Retry running the SQL if there is a time-out up to 3-times.

"""


TEMPLATE_FILE_PER_APP = (
    "./sql_templates/template_generate_per_app_metrics_for_report_date.sql"
)

TEMPLATE_FILE_MAIN = "./sql_templates/template_generate_metrics_for_report_date.sql"


def lambda_handler(event, context):
    session = boto3.Session()

    target_week_date = event["TARGET_DATE"]
    report_dates = get_report_dates_from_target_date(target_week_date)

    params = {
        "region": event["REGION"],
        "workgroup": event["WORKGROUP"],
        "database": event["DATABASE"],
        "env": event["ENV"],
        "basename_main": event["BASENAME_MAIN"],
        "basename_per_app": event["BASENAME_PER_APP"],
        "report_dates": report_dates,
    }

    print("##")
    print("## EVENT: " + str(event))
    print("##")

    # Update/create PER_APP table
    success_flag = update_or_create_metrics_table(
        session, params, params["basename_per_app"], TEMPLATE_FILE_PER_APP
    )

    if success_flag:
        print("## SUCCESS: PER_APP TABLE was updated/created!")
    else:
        print("## FAIL: PER_APP TABLE update/create un-successful after retries!")
        return {
            "STATUS": "FAIL",
            "DETAIL": "PER_APP table create/update was un-successful after retries!",
        }

    # Update/create MAIN table
    success_flag = update_or_create_metrics_table(
        session, params, params["basename_main"], TEMPLATE_FILE_MAIN
    )

    if success_flag:
        print("## SUCCESS: MAIN TABLE was updated/created!")
    else:
        print("## FAIL: MAIN TABLE update/create un-successful after retries!")
        return {
            "STATUS": "FAIL",
            "DETAIL": "MAIN table create/update was un-successful after retries!",
        }

    return {
        "STATUS": "SUCCESS",
        "DETAIL": "Metric tables are ready for refresh in QuickSight!",
    }


"""
Call / Test lambda handler with params for local development.

Edit and use the following params when testing and developing locally.

NOTE: These params are not used when launched via AWS Lambda.

When launching via AWS Lambda you must pass the parameters dictionary
via the "event". This can be included with the Lambda TEST parameters or
via the EventBridge caller.
"""
event = {
    "REGION": "us-east-1",
    "WORKGROUP": "bb2",
    "DATABASE": "bb2",
    "ENV": "impl",
    "BASENAME_MAIN": "global_state_copy1",
    "BASENAME_PER_APP": "global_state_per_app_copy1",
}
target_date_list = [
    "2023-01-16",
]

for target_date in target_date_list:
    event["TARGET_DATE"] = target_date
    print("## UPDATING FOR TARGET_DATE:  ", target_date)
    context = None
    status = lambda_handler(event, context)
    print("##")
    print("## STATUS:  ", status)
    print("##")
