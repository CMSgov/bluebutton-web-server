import argparse
import dateutil.parser
import errno
import json
import os
import uuid

from csv import reader

import sys

parser = argparse.ArgumentParser(
    description="Utility script to convert exported Splunk (.json) or Cloudwatch"
                " Insights (.csv) logs to BFD-Insights JSON files for upload to S3."
)
parser.add_argument(
    "--input-file",
    "-i",
    help="The name of the input file.",
    type=str,
)
parser.add_argument(
    "--output-dir-path", "-o", help="The path of the output directory.", type=str
)

args = parser.parse_args()


INPUT_FILE_NAME = args.input_file if args.input_file else ""

OUTPUT_DIR_PATH = args.output_dir_path if args.output_dir_path else "output"


OUTPUT_DT_DIR_FORMAT = "dt=%Y/%m/%d/%H/"

OUTPUT_FILE_PREFIX = "bfd-insights-bb2-"

OUTPUT_FILE_POSTFIX = "-perf-mon-1-"


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


def file_output(out_dict, time_of_event, env):
    global last_dt_dir_name
    global last_out_filename

    time_str = time_of_event.strftime("%Y-%m-%d-%H-%M-%S")
    dt_dir_name = time_of_event.strftime(OUTPUT_DT_DIR_FORMAT)

    if dt_dir_name == last_dt_dir_name:
        out_filename = last_out_filename
    else:
        out_filename = (
            OUTPUT_DIR_PATH
            + "/events-"
            + env
            + "-perf-mon"
            + "/"
            + dt_dir_name
            + OUTPUT_FILE_PREFIX
            + env
            + OUTPUT_FILE_POSTFIX
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


root, ext = os.path.splitext(INPUT_FILE_NAME)
if ext in [".json", ".JSON"]:
    print("")
    print("PROCESSING Splunk logs from .json input file:  ", INPUT_FILE_NAME)
    print("")
    input_file = open(INPUT_FILE_NAME, newline="")
    csv_reader = None


elif ext in [".csv", ".CSV"]:
    print("")
    print("PROCESSING Cloudwatch logs from .csv input file:  ", INPUT_FILE_NAME)
    print("")
    input_file = open(INPUT_FILE_NAME, newline="")
    csv_reader = reader(input_file)
    header = next(csv_reader)
else:
    print("")
    print("ERROR:  INPUT_FILE_NAME must have extension .csv or .json !!!")
    print("")
    sys.exit(1)

while True:
    output_dict = {}

    if csv_reader is None:

        line = input_file.readline()

        # Exit at EOF
        if not line:
            break

        # Get the raw string from top level json
        event_raw = json.loads(line).get("result").get("_raw")

        # Get dict from raw string
        event_dict = json.loads(event_raw)

        if event_dict is None:
            raise Exception("Got None for input line:  " + line)
    else:
        try:
            line = next(csv_reader)
        except StopIteration:
            # Exit at EOF
            break

        # Get message dict from  2nd list element
        event_dict = json.loads(line[1])

    # Get fields from message part of event
    message = event_dict.get("message")

    # Get time of event from group timestamp string
    time_of_event = dateutil.parser.parse(event_dict.get("time"))

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

    # Get ENV for file naming.
    env = event_dict.get("env")

    file_output(out_dict, time_of_event, env)
