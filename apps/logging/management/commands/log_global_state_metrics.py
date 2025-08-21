from datetime import datetime, timezone
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

    def handle(self, *args, **options):
        # Timestamp used to group both types of logging events from this command
        group_timestamp = format_timestamp(datetime.now())
       
        report_flag = False if options.get("no_report", None) else True

        log_global_state_metrics(group_timestamp, report_flag)
