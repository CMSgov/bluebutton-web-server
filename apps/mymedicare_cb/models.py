import logging
from django.db import models
from django.contrib.auth.models import User, Group
from rest_framework import exceptions
from apps.accounts.models import UserProfile
from apps.fhir.authentication import convert_sls_uuid
from apps.fhir.server.authentication import authenticate_crosswalk, match_hicn_hash
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from apps.fhir.bluebutton.models import Crosswalk, hash_hicn
from apps.fhir.bluebutton.utils import get_resourcerouter

logger = logging.getLogger('hhs_server.%s' % __name__)


def get_and_update_user(user_info):
    """
    This is an example of Google style.

    Args:
        user_info: This is the first param.

    Returns:
        This is a description of what is returned.

    Raises:
        KeyError: If an expected key is missing from user_info.
    """
    subject = user_info['sub']
    try:
        user = User.objects.get(username=subject)
        return user
    except User.DoesNotExist:
        pass

    hicn = user_info['hicn']
    given_name = user_info['given_name']
    last_name = user_info['family_name']
    email = user_info['email']

    hicn_hash = hash_hicn(hicn)
    try:
        fhir_id, backend_data = match_hicn_hash(hicn_hash)
    except exceptions.NotFound:
        fhir_id = None

    fhir_source = get_resourcerouter()

    user = User(username=subject,
                first_name=user_info['given_name'],
                last_name=user_info['family_name'],
                email=user_info['email'])
    user.set_unusable_password()
    user.save()
    Crosswalk.objects.create(user=user,
                             fhir_source=fhir_source,
                             user_id_hash=hicn_hash,
                             fhir_id=fhir_id)

    # Extra user information
    UserProfile.objects.create(
            user=user, user_type='BEN') # TODO: remvoe the idea of UserProfile
    # TODO: magic strings are bad
    group = Group.objects.get(name='BlueButton') # TODO: these do not need a group
    user.groups.add(group)

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

    return user


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
