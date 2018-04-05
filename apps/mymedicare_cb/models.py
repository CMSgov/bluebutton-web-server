import requests
import logging
from django.db import models
from django.contrib.auth.models import User, Group
from apps.accounts.models import UserProfile
from apps.fhir.authentication import convert_sls_uuid
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter, FhirServerAuth

__author__ = "Alan Viars"

logger = logging.getLogger('hhs_server.%s' % __name__)


def get_and_update_user(user_info):
    try:
        user = User.objects.get(username=convert_sls_uuid(user_info['sub']))
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
        user = User(username=user_info['sub'][9:36], password='',
                    first_name=user_info['given_name'],
                    last_name=user_info['family_name'],
                    email=user_info['email'])
        user.save()
    up, created = UserProfile.objects.get_or_create(
        user=user, user_type='BEN')
    group = Group.objects.get(name='BlueButton')
    user.groups.add(group)
    # Log in the user
    user.backend = 'django.contrib.auth.backends.ModelBackend'

    # Determine patient_id
    fhir_source = get_resourcerouter()
    crosswalk, g_o_c = Crosswalk.objects.get_or_create(
        user=user, fhir_source=fhir_source)
    hicn = user_info.get('hicn', "")
    crosswalk.user_id_hash = hicn
    crosswalk.save()

    auth_state = FhirServerAuth(None)
    certs = (auth_state['cert_file'], auth_state['key_file'])

    # URL for patient ID.
    url = fhir_source.fhir_url + \
        "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
        crosswalk.user_id_hash + \
        "&_format=json"
    response = requests.get(url, cert=certs, verify=False)

    if 'entry' in response.json() and response.json()['total'] == 1:
        fhir_id = response.json()['entry'][0]['resource']['id']
        crosswalk.fhir_id = fhir_id
        crosswalk.save()

        logger.info("Success:Beneficiary connected to FHIR")
    else:
        logger.error("Failed to connect Beneficiary "
                     "to FHIR")

    # Get first and last name from FHIR if not in OIDC Userinfo response.
    if user_info['given_name'] == "" or user_info['family_name'] == "":
        if 'entry' in response.json():
            if 'name' in response.json()['entry'][0]['resource']:
                names = response.json()['entry'][0]['resource']['name']
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
