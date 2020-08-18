import logging
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from apps.accounts.models import UserProfile
from apps.fhir.server.authentication import match_fhir_id
from apps.fhir.bluebutton.models import Crosswalk
from .loggers import log_get_and_update_user, log_create_beneficiary_record

logger = logging.getLogger('hhs_server.%s' % __name__)


def get_and_update_user(subject, mbi_hash, hicn_hash, first_name, last_name, email, request=None):
    """
    Find or create the user associated
    with the identity information from the ID provider.

    Args:
        Identity parameters passed in from ID provider.

        subject = ID provider's sub or username
        mbi_hash = Previously hashed mbi
        hicn_hash = Previously hashed hicn
        first_name
        last_name
        email
        request - request from caller to pass along for logging info.
    Returns:
        A User
    Raises:
        KeyError: If an expected key is missing from user_info.
        KeyError: If response from fhir server is malformed.
        AssertionError: If a user is matched but not all identifiers match.
    """
    # Match a patient identifier via the backend FHIR server
    fhir_id, hash_lookup_type = match_fhir_id(mbi_hash=mbi_hash, hicn_hash=hicn_hash, request=request)

    try:
        # Does an existing user and crosswalk exist for SLS username?
        user = User.objects.get(username=subject)

        # TODO: Replace asserts with exception handling.
        if user.crosswalk.user_hicn_hash != hicn_hash:
            mesg = "Found user's hicn did not match"
            log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
        assert user.crosswalk.user_hicn_hash == hicn_hash, "Found user's hicn did not match"

        if user.crosswalk.fhir_id != fhir_id:
            mesg = "Found user's fhir_id did not match"
            log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
        assert user.crosswalk.fhir_id == fhir_id, "Found user's fhir_id did not match"

        if user.crosswalk.user_mbi_hash is not None:
            if user.crosswalk.user_mbi_hash != mbi_hash:
                mesg = "Found user's mbi did not match"
                log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
            assert user.crosswalk.user_mbi_hash == mbi_hash, "Found user's mbi did not match"
        else:
            # Previously stored value was None/Null and mbi_hash != None, update just the mbi hash.
            if mbi_hash is not None:
                mesg = "UPDATE mbi_hash since previous value was NULL"
                log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
                user.crosswalk.user_mbi_hash = mbi_hash
                user.crosswalk.user_id_type = hash_lookup_type
                user.crosswalk.save()

        # Update hash type used for lookup, if it has changed from last match.
        if user.crosswalk.user_id_type != hash_lookup_type:
            mesg = "UPDATE user_id_type as it has changed from the previous lookup value"
            log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
            user.crosswalk.user_id_type = hash_lookup_type
            user.crosswalk.save()

        mesg = "RETURN existing beneficiary record"
        log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
        return user
    except User.DoesNotExist:
        pass

    user = create_beneficiary_record(username=subject,
                                     user_hicn_hash=hicn_hash,
                                     user_mbi_hash=mbi_hash,
                                     fhir_id=fhir_id,
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email,
                                     user_id_type=hash_lookup_type)

    mesg = "CREATE beneficiary record"
    log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg)
    return user


# TODO default empty strings to null, requires non-null constraints to be fixed
def create_beneficiary_record(username=None,
                              user_hicn_hash=None,
                              user_mbi_hash=None,
                              fhir_id=None,
                              first_name="",
                              last_name="",
                              email="",
                              user_id_type="H"):

    # Validate argument values. TODO: Replace asserts with exception handling.
    if username is None:
        mesg = "username can not be None"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
    assert username is not None

    if username == "":
        mesg = "username can not be an empty string"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
    assert username != ""

    if user_hicn_hash is None:
        mesg = "user_hicn_hash can not be None"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        assert user_hicn_hash is not None
    else:
        if len(user_hicn_hash) != 64:
            mesg = "incorrect user HICN hash format"
            log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        assert len(user_hicn_hash) == 64, "incorrect user HICN hash format"

    # If mbi_hash is not NULL, perform length check.
    if user_mbi_hash is not None:
        if len(user_mbi_hash) != 64:
            mesg = "incorrect user MBI hash format"
            log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        assert len(user_mbi_hash) == 64, "incorrect user MBI hash format"

    if fhir_id is None:
        mesg = "fhir_id can not be None"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
    assert fhir_id is not None

    if fhir_id == "":
        mesg = "fhir_id can not be an empty string"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
    assert fhir_id != ""

    if User.objects.filter(username=username).exists():
        mesg = "user already exists"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise ValidationError(mesg, username)

    if Crosswalk.objects.filter(_user_id_hash=user_hicn_hash).exists():
        mesg = "user_hicn_hash already exists"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise ValidationError(mesg, user_hicn_hash)

    # If mbi_hash is not NULL, perform check for duplicate
    if user_mbi_hash is not None:
        if Crosswalk.objects.filter(_user_mbi_hash=user_mbi_hash).exists():
            mesg = "user_mbi_hash already exists"
            log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
            raise ValidationError(mesg, user_hicn_hash)

    if fhir_id and Crosswalk.objects.filter(_fhir_id=fhir_id).exists():
        mesg = "fhir_id already exists"
        log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise ValidationError(mesg, fhir_id)

    with transaction.atomic():
        user = User(username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email)
        user.set_unusable_password()
        user.save()
        Crosswalk.objects.create(user=user,
                                 user_hicn_hash=user_hicn_hash,
                                 user_mbi_hash=user_mbi_hash,
                                 fhir_id=fhir_id,
                                 user_id_type=user_id_type)

        # Extra user information
        # TODO: remove the idea of UserProfile
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
