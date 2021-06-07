import json
import logging

from apps.dot_ext.models import get_application_counts, get_application_require_demographic_scopes_count
from apps.fhir.bluebutton.models import check_crosswalks
from django.conf import settings


"""
  Logger and logging function for waffle flags, switches
"""
waffle_event_logger = logging.getLogger('audit.waffle.event')


def log_v2_blocked(user=None, path=None, app=None, err=None, **kwargs):
    log_dict = {"type": "v2_blocked",
                "user": str(user) if user else None,
                "path": path if user else None,
                "app_id": app.id if app else None,
                "app_name": str(app.name) if app else None,
                "dev_id": str(app.user.id) if app else None,
                "dev_name": str(app.user.username) if app else None,
                "response_code": err.status_code,
                "message": str(err) if err else None}
    log_dict.update(kwargs)
    waffle_event_logger.info(json.dumps(log_dict))


"""
  Logger functions for logging  module
"""
logger = logging.getLogger('audit.global_state_metrics')


# For use in apps/logging/management/commands/log_global_metrics.py management command
def log_global_state_metrics(group_timestamp=None):
    crosswalk_counts = check_crosswalks()
    application_counts = get_application_counts()
    require_demographic_scopes_count = get_application_require_demographic_scopes_count()

    log_dict = {"type": "global_state_metrics",
                "group_timestamp": group_timestamp,
                "real_bene_cnt": crosswalk_counts.get('real', None),
                "synth_bene_cnt": crosswalk_counts.get('synthetic', None),
                "global_apps_active_cnt": application_counts.get('active_cnt', None),
                "global_apps_inactive_cnt": application_counts.get('inactive_cnt', None),
                "global_apps_require_demographic_scopes_cnt": require_demographic_scopes_count, }

    if settings.LOG_JSON_FORMAT_PRETTY:
        logger.info(json.dumps(log_dict, indent=2))
    else:
        logger.info(json.dumps(log_dict))
