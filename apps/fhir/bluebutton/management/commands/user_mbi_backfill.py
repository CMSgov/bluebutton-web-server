from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_patient_by_id
import apps.logging.request_logger as bb2logging
from django.test import RequestFactory

import logging
from typing import List
import requests


logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

FHIR_BASE_URL = "https://{ENV}.bluebutton.cms.gov/v2/fhir/"

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
        batch_size = 1
        dry_run= True
        env = 'test'
        script_url = FHIR_BASE_URL.format(ENV=env)

        print("batch size: ", batch_size)
        print("dry_run: ", dry_run)
        print("env: ", env)
        print("script_url: ", script_url)
        records = self.retrieve_records(batch_size)
        self.process_records(records, script_url)

    def retrieve_records(self, batch_size: int) -> List[Crosswalk]:
        null_mbi_records = Crosswalk.objects.filter(_user_mbi__isnull=True)[:batch_size]
        print("NUM RECS: ", len(null_mbi_records))
        return null_mbi_records
    
    def process_records(self, crosswalk_records: List[Crosswalk], script_url: str) -> None:
        for crosswalk in crosswalk_records:
            try:
                patient_info = 0
                fhir_id = crosswalk.fhir_id
                rf = RequestFactory()
                request = rf.get("/")
                print("fhir_id: ", fhir_id)
                if not fhir_id:
                    print("can't update this record, no fhir_id")
                    continue
                patient_info = get_patient_by_id(fhir_id, request)
                print("patient_info: ", patient_info)

            except Exception as e:
                print("error: ", e)
                continue
