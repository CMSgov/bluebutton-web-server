import random
import time
import uuid

from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand

from apps.dot_ext.models import AuthFlowUuidCopy

def generate_authflowuuid_records(start_date_str, sample_size):
    #
    # simulate a large dot_ext_auditflowuuid table with fequent insert + delete (50%) plus insert without delete (50%)
    #
    start_date = datetime.fromisoformat(start_date_str)
    start_date = start_date.replace(tzinfo=timezone.utc)
    date_now = datetime.now()
    date_now = date_now.replace(tzinfo=timezone.utc)
    days_elapsed = date_now - start_date
    print("Started date: {}, days elapsed: {}".format(start_date, days_elapsed.days))
    tx_per_day = sample_size//days_elapsed.days
    tx_cnt = 0 
    the_date = start_date
    insert_delete = 0
    insert_only = 0
    start_t = time.time()
    for i in range(sample_size):
        tx_cnt += 1
        if tx_cnt == tx_per_day:
            the_date += timedelta(days=1)
            tx_cnt = 0
        the_uuid = str(uuid.uuid4())
        AuthFlowUuidCopy.objects.create(
            auth_uuid = the_uuid,
            created = the_date,
        )
        if bool(random.getrandbits(1)):
            insert_delete += 1
            AuthFlowUuidCopy.objects.get(auth_uuid = the_uuid).delete()
        else:
            insert_only += 1
        print(i, end='\r')
    
    end_t = time.time()
    print("start date = {}, end_date = {}, insert_delete = {}, insert_only = {}, time elapsed (sec) = {}".format(start_date, the_date, insert_delete, insert_only, end_t - start_t))


class Command(BaseCommand):
    help = ('Generate records (as specified by --count) for table dot_ext_authflowuuid: '
            'with 50% inserted then deleted simulating authflowuuid from a completed auth flow and '
            'other 50% inserted and remained in the table simulating an incomplete auth flow.')
    
    def add_arguments(self, parser):
        parser.add_argument("-s", "--start-date", help="Start time stamp of the auth flow uuid records yyyy-mm-dd, e.g. '2020-11-12'")
        parser.add_argument("-c", "--count", type=int, default=30000, help="Total number of auth flow uuid records inserted and then deleted, inserted and remained in the table")

    def handle(self, *args, **options):
        start_date_str = options["start_date"] if options["start_date"] else "2020-11-12"
        record_count = options["count"]
        generate_authflowuuid_records(start_date_str, record_count)
