from django.core.management.base import BaseCommand
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_patient_by_id
import apps.logging.request_logger as bb2logging
from django.test import RequestFactory

import logging
from typing import List, Optional, Dict, Any


logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

FHIR_BASE_URL = "https://{ENV}.bluebutton.cms.gov/v2/fhir/"
MBI_URL = "http://hl7.org/fhir/sid/us-mbi"

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
            '--dry-run',
            type=bool,
            default=True,
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--env',
            type=str,
            default="test",
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        # batch_size = options['batch_size']
        # dry_run = options['dry-run']
        # env = options['env']
        batch_size = 10
        dry_run = False
        env = 'test'
        script_url = FHIR_BASE_URL.format(ENV=env)
        logger.info("batch size %s" % (batch_size))
        logger.info("env %s" % (env))
        logger.info("script_url %s" % (script_url))

        records = self.retrieve_records(batch_size)
        self.process_records(records, script_url, dry_run)

    def retrieve_records(self, batch_size: int) -> List[Crosswalk]:
        null_mbi_records = Crosswalk.objects.filter(_user_mbi__isnull=True)[:batch_size]
        logger.info("# of records returned %s" % (len(null_mbi_records)))
        return null_mbi_records
    
    def process_records(self, crosswalk_records: List[Crosswalk], script_url: str, dry_run: bool) -> None:
        for crosswalk in crosswalk_records:
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
                if user_mbi and not dry_run:
                    self.update_mbi(user_mbi, crosswalk)
                else:
                    logger.info("MBI not found, can't update crosswalk record for fhir_id = %s" % (fhir_id))

            except Exception as e:
                logger.error("error in process: %s" % (e))
                continue

    def extract_mbi(self, patient_info: Dict[str, Any]) -> Optional[str]:
        for identifier in patient_info.get("identifier", []):
            if identifier.get("system") == MBI_URL:
                return identifier.get("value")
        return None
    
    def update_mbi(self, user_mbi: str, crosswalk: Crosswalk) -> None:
        crosswalk._user_mbi = user_mbi
        crosswalk.save()
