from django.core.management.base import BaseCommand
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_patient_by_id
import apps.logging.request_logger as bb2logging
from django.test import RequestFactory

import logging
from time import sleep
from typing import List, Optional, Dict, Any
import requests


logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

MBI_URL = "http://hl7.org/fhir/sid/us-mbi"
MAX_RETRIES = 3
DEFAULT_SLEEP = 5

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
        null_mbi_records = Crosswalk.objects.filter(_user_mbi__isnull=True)[:batch_size]
        logger.info("# of records returned %s" % (len(null_mbi_records)))
        return null_mbi_records
    
    def process_records(self, crosswalk_records: List[Crosswalk], execute: bool) -> None:
        for crosswalk in crosswalk_records:
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    patient_info = 0
                    fhir_id = crosswalk.fhir_id
                    rf = RequestFactory()
                    request = rf.get("/")
                    logger.info("fhir_id %s" % (fhir_id))
                    if not fhir_id:
                        print("can't update this record, no fhir_id")
                        continue
                    
                    patient_info = get_patient_by_id(fhir_id, request)
                    logger.info("patient_info %s" % (patient_info))
                    user_mbi = self.extract_mbi(patient_info)

                    logger.info("user_mbi %s" % (user_mbi))
                    if user_mbi:
                        if execute:
                            self.update_mbi(user_mbi, crosswalk)
                        else:
                            logger.info("Not performing update - execute flag set to false")
                    else:
                        logger.info("MBI not found, can't update crosswalk record for fhir_id = %s" % (fhir_id))
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

    def extract_mbi(self, patient_info: Dict[str, Any]) -> Optional[str]:
        for identifier in patient_info.get("identifier", []):
            if identifier.get("system") == MBI_URL:
                return identifier.get("value")
        return None
    
    def update_mbi(self, user_mbi: str, crosswalk: Crosswalk) -> None:
        crosswalk._user_mbi = user_mbi
        crosswalk.save()
