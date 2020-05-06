from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.accounts.models import UserIdentificationLabel
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from apps.authorization.models import update_grants


def create_user(user_label):

    if User.objects.filter(username="fred").exists():
        User.objects.filter(username="fred").delete()
## I am a developer working on behalf of my organization
## I am a developer checking out Blue Button for fun
## I am a student
## I am part of an organization but am not a developer
## I am a Medicare beneficiary
## Other

#     u = User.objects.create_user(username="fred",
#                                  first_name="Fred",
#                                  last_name="Flinstone",
#                                  email='fred@example.com',
#                                  password="foobarfoobarfoobar",)
#     UserProfile.objects.create(user=u,
#                                user_type="BEN",
#                                create_applications=True,
#                                password_reset_question_1='1',
#                                password_reset_answer_1='blue',
#                                password_reset_question_2='2',
#                                password_reset_answer_2='Frank',
#                                password_reset_question_3='3',
#                                password_reset_answer_3='Bentley')

#     u.groups.add(group)
#     c, g_o_c = Crosswalk.objects.get_or_create(user=u,
#                                                _fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID,
#                                                _user_id_hash="139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130")
#     return u


# class Command(BaseCommand):
#     help = 'Populate user identification label table with roles for blue button developer sign up form'

#     def handle(self, *args, **options):
#         lb = create_user_id_labels()
