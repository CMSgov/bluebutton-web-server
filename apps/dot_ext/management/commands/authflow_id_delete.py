import time
from django.db import connection

from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand

import apps.logging.request_logger as logging


logger = logging.getLogger(logging.AUDIT_AUTHFLOW_ID_CLEANUP_LOGGER)


TARGET_TABLE_COPY = "dot_ext_authflowuuidcopy"
TARGET_TABLE = "dot_ext_authflowuuid"
DELETE_WITH_LIMIT = "DELETE FROM {table_name} WHERE auth_uuid IN (SELECT auth_uuid FROM {table_name} WHERE created < '{age_date}'::date ORDER BY created LIMIT {limit_on_delete})"


def delete_authflow_uuid_table(age, limit_on_delete, simulation):
    '''
    Delete aged authflow uuid records from table dot_ext_authflowuuid
    note, dead rows (records marked as deleted) cleanup and space reclaim will be done administratively
    via AWS auto vacuum.
    '''

    days_before = date.today()-timedelta(days=age)
    delete_sql = DELETE_WITH_LIMIT.format(table_name=TARGET_TABLE if not simulation else TARGET_TABLE_COPY, age_date=days_before.strftime("%m/%d/%Y"), limit_on_delete=limit_on_delete)

    start_t = time.time()

    with connection.cursor() as cursor:
        cursor.execute(delete_sql)
        rowcount_deleted = cursor.rowcount
        end_t = time.time()
        log_dict = {"type": "aged_authflow_id_deleted",
                    "start_time": str(datetime.fromtimestamp(start_t)),
                    "end_time": str(datetime.fromtimestamp(end_t)),
                    "elapsed_time": end_t - start_t,
                    "age": age,
                    "limit_on_delete": limit_on_delete,
                    "simulation": simulation,
                    "deleted_count": rowcount_deleted,}
        logger.info(log_dict)


class Command(BaseCommand):
    help = ('Delete aged dot_ext_authflowuuid table records.')
    
    def add_arguments(self, parser):
        parser.add_argument("-a", "--age", type=int, default=30, help="Age (in days) of authflow uuid records qualified for deletion.")
        parser.add_argument("-l", "--limit", type=int, default=30000, help="Limit on number of delete allowed for one run.")
        parser.add_argument("-s", "--simulate", action='store_true', help="Perform delete on 'AuthFlowUuidCopy' (table: dot_ext_authflowuuidcopy) - for local simulation.")

    def handle(self, *args, **options):
        age = options["age"] if options["age"] else 30
        limit_on_delete = options["limit"] if options["limit"] else 30000
        simulation = options["simulate"]
        delete_authflow_uuid_table(age, limit_on_delete, simulation)
