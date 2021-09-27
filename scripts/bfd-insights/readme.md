# HOW-TO: Convert Splunk logging to BFD-Insights

The `convert_logs_from_splunk.py` Python utility program can be used to convert logs exported from Splunk in to a format that can be imported in to the BB2 BFD-Insights S3 folders.


Please reference the BFD-Insights confluence documentation for additional details.


The following is a general procedure for converting the logging:

## 1. Perform a search in Splunk for the logging events you want to export.

For example, if we are wanting the "global_state_metrics" type log events.

Use this Splunk search:

```
index=bluebutton source="/var/log/pyapps/perf_mon.log*" host=* env=prod | search message.type=global_state_metrics | reverse
```

Then select the date & time range.

## 2. Export the Splunk search events to a file locally.

From Splunk do the following:

* Select "Export" from the pull down menu items.
* Select "JSON" format.
* Enter the filename as:  global_state_splunk_export.json

  In this example, there is only one logging event per day. Others will have multiples.

## 3. Use the "convert_logs_from_splunk.py" tool to convert the logging events to a format compatilbe with BFD-Insights.

Run the following command to get the help text:

```
python convert_logs_from_splunk.py --help
```

Run the following command for the conversion:
```
python convert_logs_from_splunk.py -i splunk_exports/global_state_splunk_export.json -df "%Y-%m" -o output_dir -t global_state_metrics
```

NOTE:  The format of the "-df" option will vary by the type of Kinesis Firehose stream. Double check the help and format of folders in S3 for the correct format to use.

## 4. Upload the converted files to S3:

You can use the AWS S3 console or the provided Bash script "upload_folders_to_s3.sh" to upload the files.

The following is an example of using the script to upload the files produced in #3.

```
cd output_dir
sh ../upload_folders_to_s3.sh s3://<S3 bucket>/databases/bb2/events-global-state/
```

## 5. From the AWS Glue console, run the related Crawler to process the uploaded files. These will be available for Athena queries and in QuickSight afterward.
