
from apps.authorization.models import DataAccessGrant
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_patient_by_mbi_hash

from django.core.management.base import BaseCommand
from django.db.models import Q, Exists, OuterRef
from django.test import RequestFactory
from django.utils.timezone import now
import logging
from oauth2_provider.models import get_refresh_token_model, get_application_model
from time import sleep
from typing import List, Optional, Dict, Any
import requests


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
        # leaving default of 0, so the limit can be applied when the query is first run
        parser.add_argument(
            '--start-user-id',
            type=int,
            default=0,
            help='Resume processing after this user_id'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        execute = options['execute']
        start_user_id = options['start_user_id']

        print("batch size %s" % (batch_size))
        print("execute %s" % (execute))

        records = self.retrieve_records(batch_size, start_user_id)
        self.process_records(records, execute)

    def retrieve_records(self, batch_size: int, start_user_id: int) -> List[Crosswalk]:
        # Subquery for users associated with research studies
        research_q = RefreshToken.objects.filter(
            application__data_access_type="RESEARCH_STUDY",
            user_id=OuterRef("user_id")
        )
        # Subquery for users associated with an active refresh tokem
        active_q = RefreshToken.objects.filter(
            revoked__isnull=True,
            user_id=OuterRef("user_id")
        )
        # Subquery for users associated with an active data access grant
        grant_q = DataAccessGrant.objects.filter(
            expiration_date__isnull=False,
            expiration_date__gte=now().date(),
            beneficiary_id=OuterRef("user_id")
        )

        qualifying_records = (
            Crosswalk.objects
            .annotate(
                in_research=Exists(research_q),
                in_active=Exists(active_q),
                in_grant=Exists(grant_q),
            )
            .filter(
                Q(in_research=True) | (Q(in_active=True) & Q(in_grant=True)),
                _user_mbi__isnull=True,
                _user_mbi_hash__isnull=False,
                user_id__gt=start_user_id
            ).order_by("user_id")
            [:batch_size]
        )
        print("# of records returned %s" % (len(qualifying_records)))

        return qualifying_records
    
    def process_records(self, crosswalk_records: List[Crosswalk], execute: bool) -> None:
        for crosswalk in crosswalk_records:
            retries = 0
            # retry three times if a RequestException occures
            while retries < MAX_RETRIES:
                try:
                    patient_info = 0
                    user_mbi_hash = crosswalk.user_mbi_hash
                    rf = RequestFactory()
                    request = rf.get("/")
                    print("fhir_id %s" % (crosswalk.fhir_id))
                    print("user_mbi_hash %s" % (user_mbi_hash))
                    if not user_mbi_hash:
                        print("can't update this record, no user_mbi_hash")
                        continue
                    
                    patient_info = get_patient_by_mbi_hash(user_mbi_hash, request)

                    user_mbi = self.extract_mbi(patient_info)

                    print("crosswalk.user_id %s" % (crosswalk.user_id))
                    if user_mbi:
                        if execute:
                            print("User %s: Updated MBI for user" % (crosswalk.user_id))
                            self.update_mbi(user_mbi, crosswalk)
                        else:
                            print("User %s: Not updating MBI - execute flag set to false" % (crosswalk.user_id))
                    else:
                        print("User %s: MBI not found, can't update crosswalk record for user" % (crosswalk.user_id))
                    break
                except requests.RequestException as e:
                    # try again 3 times, with increasingly longer sleeps, to get around any rate limit issues
                    retries += 1
                    print("Exception in request %s" % (e))
                    print("Moving on to retry number: %s" % (retries))
                    retry_sleep = DEFAULT_SLEEP * retries
                    print("Amount of sleep before trying again: %s" % (retry_sleep))
                    sleep(retry_sleep)

                except Exception as e:
                    print("error in process: %s" % (e))
                    # if it's a non requests exception, move to next record
                    break

    def extract_mbi(self, patient_bundle: Dict[str, Any]) -> Optional[str]:
        # Only proceed if total == 1
        if patient_bundle.get("total") != 1:
            return None

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
