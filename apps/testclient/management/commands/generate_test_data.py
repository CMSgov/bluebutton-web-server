from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken, RefreshToken
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import ArchivedToken, Application
from apps.authorization.models import update_grants, DataAccessGrant, ArchivedDataAccessGrant
from tqdm import tqdm

APPLICATION_SCOPES_FULL = ['patient/Patient.read', 'profile',
                           'patient/ExplanationOfBenefit.read', 'patient/Coverage.read',
                           'capability-a', 'capability-b']
APPLICATION_SCOPES_NON_DEMOGRAPHIC = ['patient/ExplanationOfBenefit.read',
                                      'patient/Coverage.read', 'capability-a', 'capability-b']

BENEFICIARY_COUNT = 10000
DEVELOPER_COUNT = 50
APPLICATION_PER_DEVELOPER = 2

def flush_database():
    """Flush all data from the database."""
    crosswalk_rows = list(Crosswalk.objects.filter(fhir_id_v2__isnull=False))

    # Modify in memory
    for crosswalk in crosswalk_rows:
        crosswalk.fhir_id_v2 = None

    # Bulk update in chunks with progress
    batch_size = 1000
    total_updated = 0

    for i in tqdm(range(0, len(crosswalk_rows), batch_size), desc='Writing to database'):
        batch = crosswalk_rows[i:i + batch_size]
        Crosswalk.objects.bulk_update(batch, ['fhir_id_v2'], batch_size=batch_size)
        total_updated += len(batch)

    print(f'Updated {total_updated} rows')

def generate_test_data(bene_count, dev_count, app_per_dev):
    #TODO
    x = bene_count

class Command(BaseCommand):
    help = ('Create dev users and create'
            ' apps for each of them, create bene users from '
            'synthetic data and crosswalk for each bene.')

    def add_arguments(self, parser):
        parser.add_argument('--flush', default=False, help='Flush the database')

    def handle(self, *args, **options):
        flush = bool(options['flush'])
        
        if flush:
            flush_database()
