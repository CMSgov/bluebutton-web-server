from django.conf import settings

import apps.logging.request_logger as logging

from apps.accounts.models import UserProfile
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application, get_application_counts, get_application_require_demographic_scopes_count
from apps.fhir.bluebutton.models import check_crosswalks, Crosswalk
from apps.logging.firehoses import BFDInsightsFirehose
from apps.logging.utils import format_timestamp


"""
  Logger functions for logging module
"""
logger = logging.getLogger(logging.AUDIT_GLOBAL_STATE_METRICS_LOGGER)


def log_global_state_metrics_top_level(group_timestamp, firehose=None):
    '''
    Used in log_global_state_metrics() to log the top level event.
    If firehose object is set, this selects output to the firehose.
    '''
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

    if firehose is None:
        logger.info(log_dict)
    else:
        firehose.put_message(log_dict)

    print("---")
    print("---    Wrote top level log entry: ", log_dict)
    print("---")


def log_global_state_metrics_applications(group_timestamp, firehose=None):
    '''
    Used in log_global_state_metrics() to log per application events.
    If firehose object is set, this selects output to the firehose.
    '''
    applications = Application.objects.all()

    count = 0
    for app in applications:
        # Get UserProfile for application's dev user
        try:
            user_profile = UserProfile.objects.get(user=app.user)
        except UserProfile.DoesNotExist:
            user_profile = None

        # Get benes having Data access grants for app
        benes = DataAccessGrant.objects.filter(application=app).values('beneficiary').distinct()

        # Get REAL benes count
        real_cnt = Crosswalk.real_objects.filter(
            user__in=[item['beneficiary'] for item in benes]).values('user', '_fhir_id').count()

        # Get SYNTH benes count
        synth_cnt = Crosswalk.synth_objects.filter(
            user__in=[item['beneficiary'] for item in benes]).values('user', '_fhir_id').count()

        log_dict = {"type": "global_state_metrics_per_app",
                    "group_timestamp": group_timestamp,
                    "id": app.id,
                    "name": app.name,
                    "created": format_timestamp(app.created),
                    "updated": format_timestamp(app.updated),
                    "active": app.active,
                    "first_active": format_timestamp(app.first_active),
                    "last_active": format_timestamp(app.last_active),
                    "require_demographic_scopes": app.require_demographic_scopes,
                    "real_bene_cnt": real_cnt,
                    "synth_bene_cnt": synth_cnt,
                    "user_id": app.user.id,
                    "user_username": app.user.username,
                    "user_date_joined": format_timestamp(app.user.date_joined),
                    "user_last_login": format_timestamp(app.user.last_login),
                    "user_organization": getattr(user_profile, "organization_name", None), }

        if firehose is None:
            logger.info(log_dict)
        else:
            firehose.put_message(log_dict)

        count = count + 1

    print("---")
    print("---    Wrote per application log entries: ", count)
    print("---")


def log_global_state_metrics(group_timestamp=None):
    '''
    For use in apps/logging/management/commands/log_global_metrics.py management command
    NOTE:  print statements are for output when run via Jenkins
    '''
    print("---")
    print("---RUNNING DJANGO COMMAND:  log_global_state_metrics")
    print("---")
    print("---")
    print("---    settings.LOG_FIREHOSE_ENABLE: ", settings.LOG_FIREHOSE_ENABLE)
    print("---")
    print("---")
    print("---  SENDING EVENTS TO STANDARD LOGGING:")
    print("---")

    log_global_state_metrics_top_level(group_timestamp=group_timestamp, firehose=None)

    log_global_state_metrics_applications(group_timestamp=group_timestamp, firehose=None)

    if settings.LOG_FIREHOSE_ENABLE:
        print("---")
        print("---  SENDING EVENTS TO BFD-INSIGHTS FIREHOSE DELIVERY STREAMS:")
        print("---")
        # Send top level state
        firehose = BFDInsightsFirehose("global-state")
        log_global_state_metrics_top_level(group_timestamp=group_timestamp, firehose=firehose)

        # Send per application state
        firehose = BFDInsightsFirehose("global-state-apps")
        log_global_state_metrics_applications(group_timestamp=group_timestamp, firehose=firehose)

    print("SUCCESS")
