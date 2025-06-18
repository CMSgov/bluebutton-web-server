from django.utils.timezone import now
from apps.accounts.models import GlobalStateMetric
from apps.logging.utils import format_timestamp
import json

def log_metric_json(json_data, timestamp=None):

    metrics_json = json_data
    if isinstance(json_data, str):
        metrics_json = json.loads(json_data)

    for item in metrics_json:
        GlobalStateMetric.objects.using('timescale').create(
            timestamp=now(),
            data=item
        )