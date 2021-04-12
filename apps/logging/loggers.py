import json
import logging

from django.conf import settings

from apps.dot_ext.models import get_application_counts, get_application_require_demographic_scopes_count
from apps.fhir.bluebutton.models import check_crosswalks


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
                "global_apps_require_demographic_scopes_count": require_demographic_scopes_count, }

    if settings.LOG_JSON_FORMAT_PRETTY:
        logger.info(json.dumps(log_dict, indent=2))
    else:
        logger.info(json.dumps(log_dict))
