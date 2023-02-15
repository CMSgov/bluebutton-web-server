import boto3

from utils.utils import (
    get_report_dates_from_target_date,
    check_table_exists,
    check_table_for_report_date_entry,
    update_or_create_table_for_report_date,
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


def update_or_create_metrics_table(session, params, table_basename, template_file):

    print("##")
    print(
        "## --- UPDATE/CREATE TABLE:  "
        + params["database"]
        + "."
        + params["env"]
        + "_"
        + table_basename
    )
    print("##")

    # Check if per_app table already exists
    table_exists = check_table_exists(session, params, table_basename)
    print("## table_exists:  ", table_exists)

    # Update the per_app table if an entry does not already exist.
    success_flag = False
    for attempt_count in range(3):
        # NOTE: Retry SQL run 3x for random Athena time-out issue.
        print("## SQL RUN ATTEMPT:  ", attempt_count + 1)
        if table_exists:
            if check_table_for_report_date_entry(session, params, table_basename):
                print("## TABLE already has entry for report_date. Skipping...")
            else:
                print("## Updating TABLE...")
                # Update table
                update_or_create_table_for_report_date(
                    session, params, table_basename, template_file, table_exists
                )
        else:
            # Create table
            print("## Creating new TABLE...")
            update_or_create_table_for_report_date(
                session, params, table_basename, template_file, table_exists
            )

        # Checking if table was updated with SQL results
        if check_table_for_report_date_entry(session, params, table_basename):
            success_flag = True
            break

    return success_flag


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
    "ENV": "prod",
    "BASENAME_MAIN": "global_state_new1",
    "BASENAME_PER_APP": "global_state_per_app_new1",
    "TARGET_DATE": "2023-01-09",
}
context = None
status = lambda_handler(event, context)

print("##")
print("## STATUS:  ", status)
print("##")
