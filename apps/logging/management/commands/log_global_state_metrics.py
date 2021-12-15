from datetime import datetime, timezone
from django.core.management.base import BaseCommand

from apps.logging.loggers import log_global_state_metrics
from apps.logging.utils import format_timestamp


class Command(BaseCommand):
    help = (
        "Managment command to log global state type metrics when called on a schedule."
    )

    def handle(self, *args, **options):
        # Timestamp used to group both types of logging events from this command
        group_timestamp = format_timestamp(datetime.now())

        log_global_state_metrics(group_timestamp)
