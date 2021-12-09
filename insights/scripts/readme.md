# HOW-TO: Convert Cloudwatch or Splunk Logging From Exports to BFD-Insights S3 JSON Files

The `convert_logs_to_json_for_insights_s3.py` Python utility program can be used to convert logs exported from either Cloudwatch or Splunk in to a format that can be imported/copied in to the BB2 BFD-Insights S3 folders.


Please reference the BFD-Insights confluence documentation for additional details.


The following is a general procedure for converting the logging:

## 1. If exporting log event records from Cloudwatch (preferred method!)

* Go to the AWS CloudWatch console `Logs insights` area.
* Choose the targe log group, such as `/bb/impl/app/perf_mon.log` for Sandbox application logs.
* In the query box, enter the following and modify based on the type of logs you wish to export:
    ```
    fields @timestamp, @message
    | filter message.type = 'global_state_metrics' or message.type = 'global_state_metrics_per_app'
    | sort @timestamp desc
    ```
* Select a Date or Time range.
* Click on `Run query`.
* After the query is run, you can export to a file via the `Export results` pull-down and `Download table (CSV)` option.

## 2. If exporting log event records from Splunk

* Perform a search in Splunk for the logging events you want to export.
  - For example, if we are wanting the "global_state_metrics" and "global_state_metrics_per_app" type log events.
  - Use this Splunk search:
    ```
    index=bluebutton source="/var/log/pyapps/perf_mon.log*" env=prod | search "message.type"="global_state_metrics*" | reverse
    ```
  - Then select the date & time range.

* Select "Export" from the pull down menu items.
* Select "JSON" format.
* Enter the filename as:  global_state_splunk_export.json
* In this example, there is only one logging event per day. Others will have multiples.


## 3. Use the Python utlity program to convert the logging events to a format compatible with BFD-Insights.

* Run the following command to get the help text:
    ```
    python convert_logs_to_json_for_insights_s3.py --help
    ```

* The program will detect if the input file is Cloudwatch (.csv) or Splunk (.json) based on extension.
* Run the following command for the conversion:
    ```
    python convert_logs_to_json_for_insights_s3.py -i splunk_exports/global_state_splunk_export.json -o output_dir
    ```
* The program will create an output matching the BFD-Insights S3 folder structure based on the `env` and `time` log fields.

## 4. Upload the converted files to S3:

* You can use the AWS S3 console or the provided Bash script "upload_folders_to_s3.sh" to upload the files. Note that the console method may need additional permissions for your AWS user account on the S3 bucket.
* This also uses GZIP to compress the files before uploading them.
* The following is an example of using the script to upload the files produced in #3.
    ```
    cd output_dir
    ls
    # Should see output similar to:  events-impl-perf-mon
    sh ../upload_folders_to_s3.sh s3://<S3 bucket>/databases/bb2/
    ```
* The files are recursively uploaded to the S3 bucket in the proper location.

## 5. From the AWS Glue console, run the related Crawler to process the uploaded files. These will be available for Athena queries and in QuickSight afterward.