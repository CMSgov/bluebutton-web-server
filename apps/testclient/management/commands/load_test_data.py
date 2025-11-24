from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken, RefreshToken
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import ArchivedToken
from apps.capabilities.models import ProtectedCapability
from apps.authorization.models import update_grants, ArchivedDataAccessGrant
from oauth2_provider.models import get_application_model


def flush_database():
    """Flush all data from the database."""
    print('Flushing database...')
    User.objects.all()
    get_application_model().objects.all()
    Crosswalk.objects.all()
    ProtectedCapability.objects.all()
    AccessToken.objects.all()
    RefreshToken.objects.all()
    ArchivedToken.objects.all()
    ArchivedDataAccessGrant.objects.all()
    print('Database flushed.')

class Command(BaseCommand):
    help = ('Create dev users and create'
            ' apps for each of them, create bene users from '
            'synthetic data and crosswalk for each bene.')

    def add_arguments(self, parser):
        parser.add_argument('--flush', default=False, help='Flush the database')

    def handle(self, *args, **options):
        delete = bool(options['delete'])
        
        if delete:
            flush_database()
        
        # update grants
        update_grants()
