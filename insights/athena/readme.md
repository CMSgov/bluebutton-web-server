# BFD-Insights BB2 Athena Views

In between the Kinesis Firehose log streams and QuickSights there are Athena views setup for mapping the reporting data.


## Global State per Application View

VIEW NAME:  vw_global_state_per_app

FILE:  views_sql/vw_global_state_per_app.sql

Summary:

* This is a JOIN of top level BB2 stats from the `bb2.events_global_state` table and per application stats from the `bb2.events_global_state_apps` table in athena.

* This returns sets of data grouped by `vpc` and `week_number`.

* This excludes our internal testing applications from the per application results.


## Global State View

VIEW NAME:  vw_global_state

FILE:  views_sql/vw_global_state.sql

Summary:

* This utilizis the `vw_global_state_per_app` view to produce counts of apps and bene data grouped by `vpc` & `week_number`.


# HOW-TO:  Update Athena Views For SQL Changes

The following is a general procedure for updating Athena views and QuickSight datasets.

1. Update the SQL file from the repository.

2. In the AWS Athena console, open up the "Query editor".

3. Select "bb2" from the workgroup drop-down on the query editor.

4. Under the "Data" panel, select the "bb2" database.

5. Under the "Data" panel, locate the "Views" section.

6. Select the "Show/edit query" action for the target view to be changed.

7. Copy and paste the edited SQL to replace the "CREATE OR REPLACE" block contents. NOTE: This may be enclosed in "()". 

8. RUN the query. This will replace it.

9. Login to AWS Quicksight.

10. Go to the `Datasets` section.

11. Select the data set related to the view that was modified. You can also create a new view in a similar way.

12. Click on the `Refresh now` button. This start a refresh for the dataset.

13. If there are changes to field names, you will be prompted to map the old fields to the new ones.

14. Edit your existing Analyses that are utlizing the dataset related to the changes.

15. Commit your SQL file changes back to the repository via PR.