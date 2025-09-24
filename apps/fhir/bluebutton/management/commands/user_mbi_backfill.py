
from apps.authorization.models import DataAccessGrant
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_patient_by_mbi_hash
import apps.logging.request_logger as bb2logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.test import RequestFactory
from django.utils.timezone import now
import logging
from oauth2_provider.models import get_refresh_token_model, get_application_model
from time import sleep
from typing import List, Optional, Dict, Any
import requests


logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

MBI_URL = "http://hl7.org/fhir/sid/us-mbi"
MAX_RETRIES = 3
DEFAULT_SLEEP = 5

RefreshToken = get_refresh_token_model()
Application = get_application_model()


class Command(BaseCommand):
    help = (
        "Management command to update bluebutton_crosswalk records where user_mbi column is null"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Apply DB updates'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        execute = options['execute']
        logger.info("batch size %s" % (batch_size))
        logger.info("execute %s" % (execute))

        records = self.retrieve_records(batch_size)
        self.process_records(records, execute)

    def retrieve_records(self, batch_size: int) -> List[Crosswalk]:
        # Subquery for users associated with research studies
        research_study_users = RefreshToken.objects.filter(
            application__data_access_type="RESEARCH_STUDY"
        ).values_list("user_id", flat=True)

        # Subquery for active refresh tokens
        active_users = RefreshToken.objects.filter(
            revoked__isnull=True
        ).values_list("user_id", flat=True)

        # Subquery for active access grants
        active_access_grants = DataAccessGrant.objects.filter(
            expiration_date__isnull=False,
            expiration_date__gte=now().date()
        ).values_list("beneficiary_id", flat=True)

        # Use the prior subqueries and where clauses to retrieve
        # the crosswalk records we want to update
        qualifying_records = Crosswalk.objects.filter(
            Q(user_id__in=research_study_users) |
            Q(user_id__in=active_users) |
            Q(user_id__in=active_access_grants),
            _user_mbi__isnull=True,
            _user_mbi_hash__isnull=False,
        ).exclude(
            _fhir_id__startswith="0"
        )[:batch_size]
        logger.info("# of records returned %s" % (len(qualifying_records)))

        # null_mbi_records = Crosswalk.objects.filter(_user_mbi__isnull=True)[:batch_size]
        # logger.info("# of records returned %s" % (len(null_mbi_records)))

        return qualifying_records
    
    def process_records(self, crosswalk_records: List[Crosswalk], execute: bool) -> None:
        for crosswalk in crosswalk_records:
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    patient_info = 0
                    user_mbi_hash = crosswalk.user_mbi_hash
                    rf = RequestFactory()
                    request = rf.get("/")
                    logger.info("fhir_id %s" % (crosswalk.fhir_id))
                    logger.info("user_mbi_hash %s" % (user_mbi_hash))
                    if not user_mbi_hash:
                        print("can't update this record, no user_mbi_hash")
                        continue
                    
                    patient_info = get_patient_by_mbi_hash(user_mbi_hash, request)

                    logger.info("patient_info %s" % (patient_info))
                    user_mbi = self.extract_mbi(patient_info)

                    logger.info("user_mbi %s" % (user_mbi))
                    if user_mbi:
                        if execute:
                            self.update_mbi(user_mbi, crosswalk)
                        else:
                            logger.info("Not performing update - execute flag set to false")
                    else:
                        logger.info("MBI not found, can't update crosswalk record for fhir_id = %s" % (crosswalk.fhir_id))
                    break
                except requests.RequestException as e:
                    # try again 3 times, with increasingly longer sleeps, to get around any rate limit issues
                    retries += 1
                    logger.error("Exception in request %s" % (e))
                    logger.info("Moving on to retry number: %s" % (retries))
                    retry_sleep = DEFAULT_SLEEP * retries
                    logger.info("Amount of sleep before trying again: %s" % (retry_sleep))
                    sleep(retry_sleep)

                except Exception as e:
                    logger.error("error in process: %s" % (e))
                    # if it's a non requests exception, move to next record
                    break

    def extract_mbi(self, patient_bundle: Dict[str, Any]) -> Optional[str]:
        # Only proceed if total == 1
        if patient_bundle.get("total") != 1:
            return None

        # Get the first (and only) Patient resource
        entries = patient_bundle.get("entry", [])
        if not entries:
            return None

        patient = entries[0].get("resource", {})
        identifiers = patient.get("identifier", [])

        # Look for the identifier with the MBI system
        for ident in identifiers:
            if ident.get("system") == MBI_URL:
                return ident.get("value")

        return None
    
    def update_mbi(self, user_mbi: str, crosswalk: Crosswalk) -> None:
        crosswalk._user_mbi = user_mbi
        crosswalk.save()
