from datetime import datetime
from django.core.management.base import BaseCommand

from apps.logging.loggers import log_global_state_metrics
from apps.logging.utils import format_timestamp


class Command(BaseCommand):
    help = (
        "Management command to log global state type metrics when called on a schedule."
    )

    def add_arguments(self, parser):
        # Optional argument to prevent console report in unit tests.
        parser.add_argument('-n', '--no-report', action="store_true", help='Do not include report for console.', )
        # Optional argument to post to ITS-log API
        parser.add_argument('-l', '--post-to-its-log', action="store_false", help='Post results to ITS-log API.', )

    def handle(self, *args, **options):
        # Timestamp used to group both types of logging events from this command
        group_timestamp = format_timestamp(datetime.now())
       
        report_flag = False if options.get("no_report", None) else True
        its_log_flag = False if options.get("post_to_its_log", None) else True
        print("its_log_flag: ", its_log_flag)
        log_global_state_metrics(group_timestamp, report_flag, its_log_flag)
