import logging
from django.db import models
from django.contrib.auth.models import User, Group
from rest_framework import exceptions
from apps.accounts.models import UserProfile
from apps.fhir.authentication import convert_sls_uuid
from apps.fhir.server.authentication import authenticate_crosswalk
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter

logger = logging.getLogger('hhs_server.%s' % __name__)


def get_and_update_user(user_info):
    username = convert_sls_uuid(user_info['sub'])
    try:
        user = User.objects.get(username=username)
        if not user.first_name:
            user.first_name = user_info['given_name']
        if not user.last_name:
            user.last_name = user_info['family_name']
        if not user.email:
            user.email = user_info['email']
        user.save()
    except User.DoesNotExist:
        # Create a new user. Note that we can set password
        # to anything, because it won't be checked.
        user = User(username=username, password='',
                    first_name=user_info['given_name'],
                    last_name=user_info['family_name'],
                    email=user_info['email'])
        user.set_unusable_password()
        user.save()
    UserProfile.objects.get_or_create(
        user=user, user_type='BEN')
    group = Group.objects.get(name='BlueButton')
    user.groups.add(group)
    # Log in the user
    user.backend = 'django.contrib.auth.backends.ModelBackend'

    # Determine patient_id
    fhir_source = get_resourcerouter()
    crosswalk, _ = Crosswalk.objects.get_or_create(
        user=user, fhir_source=fhir_source)
    hicn = user_info.get('hicn', "")
    crosswalk.user_id_hash = hicn
    crosswalk.save()

    try:
        backend_data = authenticate_crosswalk(crosswalk)
        # Get first and last name from FHIR if not in OIDC Userinfo response.
        if user_info['given_name'] == "" or user_info['family_name'] == "":
            if 'entry' in backend_data:
                if 'name' in backend_data['entry'][0]['resource']:
                    names = backend_data['entry'][0]['resource']['name']
                    first_name = ""
                    last_name = ""
                    for n in names:
                        if n['use'] == 'usual':
                            last_name = n['family']
                            first_name = n['given'][0]
                        if last_name or first_name:
                            user.first_name = first_name
                            user.last_name = last_name
                            user.save()
    except (UpstreamServerException, exceptions.NotFound):
        logger.error("Failed to connect Beneficiary "
                     "to FHIR")

    return user


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
