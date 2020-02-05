import logging
from django.db import models, transaction
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
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

    # raises exceptions.NotFound:
    fhir_id, backend_data = match_hicn_hash(hicn_hash)

    try:
        user = User.objects.get(username=subject)
        assert user.crosswalk.user_id_hash == hicn_hash, "Found user's hicn did not match"
        assert user.crosswalk.fhir_id == fhir_id, "Found user's fhir_id did not match"
        return user
    except User.DoesNotExist:
        pass

    first_name = user_info.get('given_name', "")
    last_name = user_info.get('family_name', "")
    email = user_info.get('email', "")

    fhir_source = get_resourcerouter()

    user = create_beneficiary_record(username=subject,
                                     user_id_hash=hicn_hash,
                                     fhir_id=fhir_id,
                                     fhir_source=fhir_source,
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email)
    return user


# TODO default empty strings to null, requires non-null constraints to be fixed
def create_beneficiary_record(username=None,
                              user_id_hash=None,
                              fhir_id=None,
                              fhir_source=None,
                              first_name="",
                              last_name="",
                              email=""):
    assert username is not None
    assert username != ""
    assert user_id_hash is not None
    assert len(user_id_hash) == 64, "incorrect user id hash format"
    assert fhir_id is not None
    assert fhir_id != ""

    if User.objects.filter(username=username).exists():
        raise ValidationError("user already exists", username)

    if Crosswalk.objects.filter(_user_id_hash=user_id_hash).exists():
        raise ValidationError("user_id_hash already exists", user_id_hash)

    if fhir_id and Crosswalk.objects.filter(_fhir_id=fhir_id).exists():
        raise ValidationError("fhir_id already exists", fhir_id)

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


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
