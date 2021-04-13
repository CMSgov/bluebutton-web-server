from datetime import datetime, timezone
from django.core.management.base import BaseCommand

from apps.logging.loggers import log_global_state_metrics

class Command(BaseCommand):
    help = 'Managment command to log global state type metrics when called on a schedule.'

    def handle(self, *args, **options):
        # Timestamp used to group multiple logging events from this command
        group_timestamp = datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()

        log_global_state_metrics(group_timestamp)
