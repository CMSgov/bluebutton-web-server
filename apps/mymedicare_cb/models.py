import logging
from django.db import models, transaction
from django.contrib.auth.models import User, Group
from rest_framework import exceptions
from apps.accounts.models import UserProfile
from apps.fhir.server.authentication import match_hicn_hash
from apps.fhir.bluebutton.models import Crosswalk, hash_hicn
from apps.fhir.bluebutton.utils import get_resourcerouter

logger = logging.getLogger('hhs_server.%s' % __name__)


def get_and_update_user(user_info):
    """
    Find or create the user associated
    with the identity information from the ID provider.

    Args:
        user_info: Identity response from the userinfo endpoint of the ID provider.

    Returns:
        A User

    Raises:
        KeyError: If an expected key is missing from user_info.
        KeyError: If response from fhir server is malformed.
        AssertionError: If a user is matched but not all identifiers match.
    """
    subject = user_info['sub']
    hicn = user_info['hicn']
    hicn_hash = hash_hicn(hicn)

    try:
        user = User.objects.get(username=subject)
        assert user.crosswalk.user_id_hash == hicn_hash, "Found user's hicn did not match"
        return user
    except User.DoesNotExist:
        pass

    first_name = user_info.get('given_name', "")
    last_name = user_info.get('family_name', "")
    email = user_info.get('email', "")

    try:
        fhir_id, backend_data = match_hicn_hash(hicn_hash)
        # Get first and last name from FHIR if not in OIDC Userinfo response.
        if first_name == "" or last_name == "":
            first_name, last_name = extract_beneficiary_names(backend_data)
    except exceptions.NotFound:
        fhir_id = None

    fhir_source = get_resourcerouter()

    user = create_beneficiary_record(username=subject,
                                     user_id_hash=hicn_hash,
                                     fhir_id=fhir_id,
                                     fhir_source=fhir_source,
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email)
    return user


def create_beneficiary_record(username=None,
                              user_id_hash=None,
                              fhir_id=None,
                              fhir_source=None,
                              first_name=None,
                              last_name=None,
                              email=None):
    with transaction.atomic():
        user = User(username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email)
        user.set_unusable_password()
        user.save()
        Crosswalk.objects.create(user=user,
                                 fhir_source=fhir_source,
                                 user_id_hash=user_id_hash,
                                 fhir_id=fhir_id)

        # Extra user information
        # TODO: remvoe the idea of UserProfile
        UserProfile.objects.create(user=user, user_type='BEN')
        # TODO: magic strings are bad
        group = Group.objects.get(name='BlueButton')  # TODO: these do not need a group
        user.groups.add(group)
    return user


def extract_beneficiary_names(patient_resource):
    if 'entry' in patient_resource:
        if 'name' in patient_resource['entry'][0]['resource']:
            names = patient_resource['entry'][0]['resource']['name']
            for n in names:
                if n['use'] == 'usual':
                    last_name = n['family']
                    first_name = n['given'][0]
                    return first_name, last_name
    return None, None


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
