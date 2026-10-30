## About this folder

The purpose of this folder is to store ETLs that are used in the its-log API. These ETLs are used to transform
data from the itslog_events table into the itslog_summary table. These different database tables help us track 
Blue Button API metrics.

There is a script within insights/scripts, called encode_etl_post_to_logging_api.py. The purpose of that script
is to take every file within the etls directory, encode it, and post it to the its-log API so the ETL can be used.

If you add a new ETL for its-log, add it to this directory. You'll also need to modify the encode_etl_post_to_logging_api.py
script (details in the script).