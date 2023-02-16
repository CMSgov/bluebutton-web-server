# BFD-Insights BB2 Athena

In between the Kinesis Firehose log streams and QuickSights there are Athena tables setup for mapping the reporting data. The reporting data is used to build dashboards and analysis in QuickSight.

## Global State per Application Table

TABLE NAME:  <test|impl|prod>_global_state_per_app

TEMPLATE:  `sql_templates/template_generate_per_app_metrics_for_report_date.sql`

NOTE: There is a separate table for each BB2 ENV enviornment (prod, impl, test).

### Summary:

* This is a JOIN of top level BB2 stats from the `bb2.events_<test|impl|prod>_perf_mon` table with type="global_state_metrics_per_app" and per application stats from the same table with type="global_state_metrics".

* This returns sets of data grouped by `vpc`, and `report_date`.

* This excludes our internal use applications from the per application results.

* To test or view results via the Athena SQL editor use the following for the target ENV:
  ```sql
  /* Show all records */
  SELECT * FROM "bb2"."<test|impl|prod>_global_state_per_app"
  ```
  ```sql
  /* Show distinct report dates */
  SELECT DISTINCT report_date FROM "bb2"."<test|impl|prod>_global_state_per_app"
  ```

## Global State Table

VIEW NAME:  <test|impl|prod>_global_state

TEMPLATE:  `sql_templates/template_generate_metrics_for_report_date.sql`

Summary:

* This utilizes the previously run `<test|impl|prod>_global_state_per_app` table results to provide counts of apps and bene data grouped by `vpc` and `report_date`.

* To test or view results via the Athena SQL editor use the following for the target ENV:
  ```sql
  /* Show all records */
  SELECT * FROM "bb2"."<test|impl|prod>_global_state"
  ```
  ```sql
  /* Show distinct report dates */
  SELECT DISTINCT report_date FROM "bb2"."<test|impl|prod>_global_state"
  ```

# Weekly Updating of the Report Tables

A scheduled AWS Lambda function is used to update the tables used for dashboards and anylysis in AWS QuickSight.

The lambda function, templates and a development tool are included in the `insights/lambdas/update_athena_metric_tables` directory.

The files in this directory are:

- `lambda_update_athena_metric_tables.py`:
  - Python Lambda function setup on a schedule in the BFD AWS account.
    - It takes parameters for the target enviornment (prod/impl/test) and metrics reporting table basenames used.
    - There is one scheduled call per environment and is run weekly.
  - This can be tested in local development. See HOW-TO example later in this README.
- `test_run_sql_template_on_athena.py`:
  - Used from the command line to run and test Athena SQL queries using a template. With this you can preview the SQL template results with out updating the reporting tables.
  - This is a tool useful when developing and adding new metrics to the template files.
- `sql_templates/template_generate_per_app_metrics_for_report_date.sql`:
  - Used to generate the per application metrics.
  - One row per application is produced.
    - These can be linked together using the `vpc` and `report_date` fields. 
- `sql_templates/template_generate_metrics_for_report_date.sql`:
  - Used to generate the top-level metrics for the report week.
  - One row is produced with the week's metrics.

# HOW-TO: Testing SQL Templates

The developer command line tool can be used to test out the templates with out updating the reporting tables.

The Python program is:  `test_run_sql_template_on_athena.py`

The command's help (via `-h` option) has info about the parameters that can be used.

The following is an example of usage for testing out the per application template using `report_date = "2023-01-09"` and `vpc = "prod"`:

```
clear;rm out.csv; python test_run_sql_template_on_athena.py -t 2023-01-09 -e prod -i sql_templates/template_generate_per_app_metrics_for_report_date.sql -o out.csv
```

NOTE: When using the `-o` option, the results are also written to a CSV file for your review. You can also view the query results and run time information via the AWS console Athena Query Editor.

NOTE: When working on the main top-level SQL template, it is expecting an entry to already exist in the related PER-APP metric table. The `-b` option can be used to specifiy the table you are working with. For example:  `-b global_state_per_app_new1`.


# Lambda Function Used to Update Report Tables

The Python Lambda program is:  `lambda_update_athena_metric_tables.py`

Lambda Summary:

- The Lambda function is installed in the BFD AWS account w/ BB2 permissions.
- On a weekly schedule, the function is called via an EventBridge schedule with parameters for the target VPC (env). 
- Runs a query to check if the per application table exists.
- Runs a query to check if entries exist for the `report_date`.
  - Skips updating the table, if entries exist.
- Updates or creates the per application table with results using the per application SQL template.
  - Retries this up to 3 times, in case there are time-out issues. Note that these occasionally occur for unknown reasons. Re-running the same query is usually successful.
- Runs a query to check if the top-level table exists.
- Runs a query to check if an entry exists for the `report_date`.
  - Skips updating the table, if an entry exists.
- Updates or creates the top-level table with results using the SQL template.
  - Retries this up to 3 times if there are time-out issues.

Lambda Parameters:

A dictionary of parameters is passed in to the Lambda function.

These parameters are:

- REGION: AWS region. Ex. "us-east-1"
- WORKGROUP: The Athena workgroup. Ex. "bb2"
- DATABASE: The database. Ex. "bb2",
- ENV: The target BB2 environment (prod/impl/test). Ex. "prod"
- BASENAME_MAIN: The basename for the top-level table. Ex. "global_state",
- BASENAME_PER_APP: The basename for the per-application table. Ex. "global_state_per_app"
- TARGET_DATE: Target report week to generate metrics for. Ex. "2023-01-09"
  - If this is blank (""), the report week will be selected based on the current date.

The following is an example dictionary:

```python
event = {
    "REGION": "us-east-1",
    "WORKGROUP": "bb2",
    "DATABASE": "bb2",
    "ENV": "prod",
    "BASENAME_MAIN": "global_state_new1",
    "BASENAME_PER_APP": "global_state_per_app_new1",
    "TARGET_DATE": "2023-01-09",
}
```

- The Lambda program can be run locally for development testing. The main part of the code has an area where the `event` parameters can be setup and tested via a call to the `lambda_handler(event, context)`. Be sure to backup the main tables and update the table basenames used when running locally for development. See HOW-TO example for a walk-through of adding new metrics later in this README. 


# HOW-TO:  Update QuickSight DataSets

The following is a general procedure for updating QuickSight datasets. After the tables are updated in Athena, they must be refreshed (manually or scheduled) to be used in QuickSight.

1. Login to AWS Quicksight.

2. Go to the `Datasets` section.

3. Select the data set related to the view that was modified. You can also create a new view in a similar way.

4. Click on the `Refresh now` button. This start a refresh for the dataset.

5. If there are changes to field names, you will be prompted to map the old fields to the new ones.

6. Edit your existing Analyses that are utlizing the dataset related to the changes. Use the SHARE and PUBLISH to update the related dashboard.


# HOW-TO:  A Walk-Through Example of Adding New Metrics

1. BACKUP the current metrics tables using the AWS Athena Query Editor.
  - Repeat for impl & test enviornments too.
  - Replace "2023_02_10" with your date.
  - This is to create a backup of tables, just in case!

```sql
/* Main (top-level) metrics table backup. */
CREATE TABLE bb2.prod_global_state_bak_2023_02_10 AS
  SELECT * FROM bb2.prod_global_state
```
```sql
/* Show report_date entries */
SELECT DISTINCT report_date FROM bb2.prod_global_state_bak_2023_02_10
```

```sql
/* PER_APP metrics table backup. */
CREATE TABLE bb2.prod_global_state_per_app_bak_2023_02_10 AS
  SELECT * FROM bb2.prod_global_state_per_app
```
```sql
/* Show report_date entries */
SELECT DISTINCT report_date FROM bb2.prod_global_state_per_app_bak_2023_02_10
```

2. Copy the current metrics tables to the following.
  - Table names:
    - bb2.prod_global_state_copy1
    - bb2.prod_global_state_per_app_copy1
  - Repeat for impl & test enviornments too.
  - These will have the schema BEFORE you add new metrics.
  - For testing purposes, exclude previous report_dates per WHERE clause.

```sql
CREATE TABLE bb2.prod_global_state_copy1 AS
  SELECT * FROM bb2.prod_global_state
    WHERE report_date < CAST('2023-01-09' as Date)
```
```sql
/* Show report_date entries */
SELECT DISTINCT report_date FROM bb2.prod_global_state_copy1
```

```sql
CREATE TABLE bb2.prod_global_state_per_app_copy1 AS
  SELECT * FROM bb2.prod_global_state_per_app
    WHERE report_date < CAST('2023-01-09' as Date)
```
```sql
/* Show report_date entries */
SELECT DISTINCT report_date FROM bb2.prod_global_state_per_app_copy1
```

3. Develop new metrics using the code and templates under: insights/lambdas/update_athena_metric_tables. See previous info in this README.

4. Test run using the `lambda_update_athena_metric_tables.py` Lambda locally.
  - Change the following `event` parameters:
  ```
    "ENV": "prod",
    "BASENAME_MAIN": "global_state_new1",
    "BASENAME_PER_APP": "global_state_per_app_new1",
    "TARGET_DATE": "2022-01-09",
  ```
  - Drop the tables, if needed.
  ```sql
  DROP TABLE bb2.prod_global_state_per_app_new1
  ```
  ```sql
  DROP TABLE bb2.prod_global_state_new1
  ```
  - Run and test the Lambda locally.
    - Source your AWS setup for the BFD account.
    - Run the following command line:
      ```
      clear; python lambda_update_athena_metric_tables.py
      ```
4. Compare the schemas to get a list of columns to add to the `_copy1` tables.
  - Show schema for `_copy1` tables.
    ```sql
    SHOW COLUMNS FROM bb2.prod_global_state_copy1
    ```
    ```sql
    SHOW COLUMNS FROM bb2.prod_global_state__per_app_copy1
    ```
  - Show schema for `_new1` tables.
    ```sql
    SHOW COLUMNS FROM bb2.prod_global_state_new1
    ```
    ```sql
    SHOW COLUMNS FROM bb2.prod_global_state__per_app_new1
    ```
5. Keep note of the metric columns and data types that were added.
  - In this example, the following columns were added to the tables:


## TODO: Continue updating this how-to in the upcoming BB2-1855 PR

As part of Jira BB2-1855, this section is to be updated with a walk through of adding in SDK metrics!
