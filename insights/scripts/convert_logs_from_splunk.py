import argparse
import dateutil.parser
import errno
import json
import os
import uuid


parser = argparse.ArgumentParser(
    description="Utility script to convert exported Splunk logs to BFD-Insights S3 JSON files."
)
parser.add_argument(
    "--splunk-json-file-in",
    "-i",
    help="The name of the Splunk JSON input file.",
    type=str,
)
parser.add_argument(
    "--output-dir-path", "-o", help="The path of the output directory.", type=str
)
parser.add_argument(
    "--output-dt-dir-format",
    "-df",
    help="The BFD insights directory DT (date/time) format."
    ' For example "%%Y-%%m-%%d" or "%%Y-%%m" used to create the "dt=2021-09-01" '
    'or "dt=2021-09/" type dir for output.',
    type=str,
)
parser.add_argument(
    "--log-type",
    "-t",
    help="The log events type to parse/include. For example: -t global_state_metrics",
    type=str,
)

args = parser.parse_args()

# Check args
if not args.log_type:
    raise Exception("--log-type argument is required! See HELP for details.")

if not args.output_dt_dir_format:
    raise Exception(
        "--output-dt-dir-format argument is required! See HELP for details."
    )


INPUT_FILE_NAME = (
    args.splunk_json_file_in if args.splunk_json_file_in else "splunk_json_in.json"
)
OUTPUT_DIR_PATH = args.output_dir_path if args.output_dir_path else "output"
OUTPUT_DT_DIR_FORMAT = args.output_dt_dir_format
LOG_TYPE = args.log_type

OUTPUT_FILE_PREFIX = "bfd-insights-bb2-"


# Globals
last_dt_dir_name = ""
last_out_filename = ""


def format_timestamp(dt):
    """
    Returns an ISO 6801 format string in UTC that works well with AWS Glue/Athena
    """
    return (
        dt.replace(microsecond=0).isoformat().replace("+00:00", "")
        if dt is not None
        else None
    )


def file_output(out_dict, time_of_event):
    global last_dt_dir_name
    global last_out_filename

    time_str = time_of_event.strftime("%Y-%m-%d-%H-%M-%S")
    dt_dir_name = "dt=" + time_of_event.strftime(OUTPUT_DT_DIR_FORMAT)

    if dt_dir_name == last_dt_dir_name:
        out_filename = last_out_filename
    else:
        out_filename = (
            OUTPUT_DIR_PATH
            + "/"
            + dt_dir_name
            + "/"
            + OUTPUT_FILE_PREFIX
            + out_dict["type"]
            + "-1-"
            + time_str
            + "-"
            + str(uuid.uuid1())
        )

    print(
        "- Appending to OUTFILE:  ", out_filename
    )  # lgtm [py/clear-text-logging-sensitive-data]

    # Make directories in path, if they don't exist.
    if not os.path.exists(os.path.dirname(out_filename)):
        try:
            os.makedirs(os.path.dirname(out_filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(out_filename, "a") as f:
        json.dump(out_dict, f)
        f.write("\n")

    # Keep track of previous file for appending multiple json events in same file
    last_dt_dir_name = dt_dir_name
    last_out_filename = out_filename


with open(INPUT_FILE_NAME, newline="") as input_file:
    print("")
    print("PROCESSING for LOG_TYPE:  ", LOG_TYPE)
    print("")

    # Loop through per line JSON entries
    for line in input_file:
        output_dict = {}

        # Get the raw string from top level json
        event_raw = json.loads(line).get("result").get("_raw")

        # Get dict from raw string
        event_dict = json.loads(event_raw)

        if event_dict is None:
            raise Exception("Got None for input line:  " + line)

        # Get fields from message part of event
        message = event_dict.get("message")

        # Is this event the correct type?
        if message.get("type") == LOG_TYPE:
            # Get time of event from group timestamp string
            time_of_event = dateutil.parser.parse(message.get("group_timestamp"))

            out_dict = {
                "time_of_event": format_timestamp(time_of_event),
                "instance_id": "i-00000000000000000",
                "image_id": "ami-00000000000000000",
                "component": "bb2.web",
                "vpc": event_dict.get("env"),
                "log_name": event_dict.get("name"),
            }

            # Merge in message fields
            out_dict.update(message)

            file_output(out_dict, time_of_event)
