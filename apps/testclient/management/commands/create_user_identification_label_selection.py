from django.core.management.base import BaseCommand
from apps.accounts.models import UserIdentificationLabel
from apps.testclient.constants import DEVELOPER_SIGNUP_ROLE_CHOICES


def create_user_identification_label():
    UserIdentificationLabel.objects.all().delete()
    for c in DEVELOPER_SIGNUP_ROLE_CHOICES:
        choice = UserIdentificationLabel.objects.create(name=c[1], slug=c[2], weight=c[0])
        print("group created %s " % (choice))


class Command(BaseCommand):
    help = 'Populate UserIdentificationLabel with choice values'

    def handle(self, *args, **options):
        create_user_identification_label()
