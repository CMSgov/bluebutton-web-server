from django.core.management.base import BaseCommand
from apps.accounts.models import UserIdentificationLabel

DEVELOPER_SIGNUP_ROLE_CHOICES = [
    (1, 'I am a developer working on behalf of my organization', 'dev-of-org'),
    (2, 'I am a developer checking out Blue Button for fun', 'dev-for-fun'),
    (3, 'I am a student', 'dev-student'),
    (4, 'I am part of an organization but am not a developer', 'person-part-of-org'),
    (5, 'I am a Medicare beneficiary', 'medicare-bene'),
    (6, 'Other', 'other'),
]

## I am a developer working on behalf of my organization
## I am a developer checking out Blue Button for fun
## I am a student
## I am part of an organization but am not a developer
## I am a Medicare beneficiary
## Other

def create_user_identification_label():
    UserIdentificationLabel.objects.all().delete()
    for c in DEVELOPER_SIGNUP_ROLE_CHOICES:
       choice = UserIdentificationLabel.objects.create(name=c[1], slug=c[2], weight=c[0])
       print("group created %s " % (choice))


class Command(BaseCommand):
    help = 'Populate UserIdentificationLabel with choice values'

    def handle(self, *args, **options):
        create_user_identification_label()
