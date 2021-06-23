import json
import logging

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from apps.accounts.models import UserProfile
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application, get_application_counts, get_application_require_demographic_scopes_count
from apps.fhir.bluebutton.models import check_crosswalks, Crosswalk


"""
  Logger functions for logging module
"""
logger = logging.getLogger('audit.global_state_metrics')


def log_global_state_metrics(group_timestamp=None):
    '''
    For use in apps/logging/management/commands/log_global_metrics.py management command
    NOTE:  print statements are for output when run via Jenkins
    '''
    print("---")
    print("---RUNNING DJANGO COMMAND:  log_global_state_metrics")
    print("---")

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

    print("---")
    print("---    Wrote top level log entry: ", log_dict)
    print("---")

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
                    "created": app.created,
                    "updated": app.updated,
                    "active": app.active,
                    "first_active": app.first_active,
                    "last_active": app.last_active,
                    "require_demographic_scopes": app.require_demographic_scopes,
                    "real_bene_cnt": real_cnt,
                    "synth_bene_cnt": synth_cnt,
                    "user_id": app.user.id,
                    "user_username": app.user.username,
                    "user_date_joined": app.user.date_joined,
                    "user_last_login": app.user.last_login,
                    "user_organization": getattr(user_profile, "organization_name", None), }

        if settings.LOG_JSON_FORMAT_PRETTY:
            logger.info(json.dumps(log_dict, indent=2, cls=DjangoJSONEncoder))
        else:
            logger.info(json.dumps(log_dict, cls=DjangoJSONEncoder))

        count = count + 1

    print("---")
    print("---    Wrote per application log entries: ", count)
    print("---")
    print("SUCCESS")
