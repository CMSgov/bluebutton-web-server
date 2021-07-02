import logging

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.accounts.models import UserProfile
from apps.dot_ext.loggers import get_session_auth_flow_trace
from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from apps.fhir.server.authentication import match_fhir_id
from .loggers import log_get_and_update_user, log_create_beneficiary_record


logger = logging.getLogger('hhs_server.%s' % __name__)


class BBMyMedicareCallbackCrosswalkCreateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BBMyMedicareCallbackCrosswalkUpdateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


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
        request = request from caller to pass along for logging info.
    Returns:
        user = The user that was existing or newly created
        crosswalk_type =  Type of crosswalk activity:
            "R" = Returned existing crosswalk record
            "C" = Created new crosswalk record
    Raises:
        KeyError: If an expected key is missing from user_info.
        KeyError: If response from fhir server is malformed.
        AssertionError: If a user is matched but not all identifiers match.
    """
    # Get auth flow session values.
    auth_flow_dict = get_session_auth_flow_trace(request)

    # Match a patient identifier via the backend FHIR server
    fhir_id, hash_lookup_type = match_fhir_id(mbi_hash=mbi_hash, hicn_hash=hicn_hash, request=request)

    # Init for types of crosswalk updates. "" = None
    crosswalk_updated = ""

    try:
        # Does an existing user and crosswalk exist for SLSx username?
        user = User.objects.get(username=subject)

        # fhir_id can not change for an existing user!
        if user.crosswalk.fhir_id != fhir_id:
            mesg = "Found user's fhir_id did not match"
            log_get_and_update_user(auth_flow_dict, "FAIL", user, fhir_id, mbi_hash, hicn_hash,
                                    hash_lookup_type, crosswalk_updated, mesg)
            raise BBMyMedicareCallbackCrosswalkUpdateException(mesg)

        # Did the hicn change?
        if user.crosswalk.user_hicn_hash != hicn_hash:
            crosswalk_updated = crosswalk_updated + "H"

        # Did the mbi change?
        if user.crosswalk.user_mbi_hash is not None:
            if user.crosswalk.user_mbi_hash != mbi_hash:
                crosswalk_updated = crosswalk_updated + "M"
        else:
            # Did the mbi change from previously stored None/Null value?
            if mbi_hash is not None:
                crosswalk_updated = crosswalk_updated + "N"

        # Update Crosswalk if there are any allowed changes or hash_type used for lookup changed.
        if user.crosswalk.user_id_type != hash_lookup_type or crosswalk_updated != "":
            # Copy pre-save values to ArchivedCrosswalk instance
            acw = ArchivedCrosswalk.objects.create(crosswalk=user.crosswalk,
                                                   _fhir_id=user.crosswalk.fhir_id,
                                                   user_id_type=user.crosswalk.user_id_type,
                                                   _user_id_hash=user.crosswalk.user_hicn_hash,
                                                   _user_mbi_hash=user.crosswalk.user_mbi_hash)
            acw.save()

            user.crosswalk.user_id_type = hash_lookup_type
            user.crosswalk.user_hicn_hash = hicn_hash
            user.crosswalk.user_mbi_hash = mbi_hash
            user.crosswalk.save()

        # Beneficiary has been successfully matched!
        mesg = "RETURN existing beneficiary record"
        log_get_and_update_user(auth_flow_dict, "OK", user, fhir_id, mbi_hash, hicn_hash,
                                hash_lookup_type, crosswalk_updated, mesg)
        return user, "R"
    except User.DoesNotExist:
        pass

    user = create_beneficiary_record(username=subject,
                                     user_hicn_hash=hicn_hash,
                                     user_mbi_hash=mbi_hash,
                                     fhir_id=fhir_id,
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email,
                                     user_id_type=hash_lookup_type,
                                     auth_flow_dict=auth_flow_dict)

    mesg = "CREATE beneficiary record"
    log_get_and_update_user(auth_flow_dict, "OK", user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, crosswalk_updated, mesg)
    return user, "C"


# TODO default empty strings to null, requires non-null constraints to be fixed
def create_beneficiary_record(username=None,
                              user_hicn_hash=None,
                              user_mbi_hash=None,
                              fhir_id=None,
                              first_name="",
                              last_name="",
                              email="",
                              user_id_type="H",
                              auth_flow_dict=None):

    if auth_flow_dict is None:
        # If None, set empty dictionary.
        auth_flow_dict = {}

    if username is None:
        mesg = "username can not be None"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if username == "":
        mesg = "username can not be an empty string"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if user_hicn_hash is None:
        mesg = "user_hicn_hash can not be None"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)
    else:
        if len(user_hicn_hash) != 64:
            mesg = "incorrect user HICN hash format"
            log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
            raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    # If mbi_hash is not NULL, perform length check.
    if user_mbi_hash is not None:
        if len(user_mbi_hash) != 64:
            mesg = "incorrect user MBI hash format"
            log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
            raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if fhir_id is None:
        mesg = "fhir_id can not be None"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if fhir_id == "":
        mesg = "fhir_id can not be an empty string"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if User.objects.filter(username=username).exists():
        mesg = "user already exists"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise ValidationError(mesg, username)

    if Crosswalk.objects.filter(_user_id_hash=user_hicn_hash).exists():
        mesg = "user_hicn_hash already exists"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
        raise ValidationError(mesg, user_hicn_hash)

    # If mbi_hash is not NULL, perform check for duplicate
    if user_mbi_hash is not None:
        if Crosswalk.objects.filter(_user_mbi_hash=user_mbi_hash).exists():
            mesg = "user_mbi_hash already exists"
            log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
            raise ValidationError(mesg, user_hicn_hash)

    if fhir_id and Crosswalk.objects.filter(_fhir_id=fhir_id).exists():
        mesg = "fhir_id already exists"
        log_create_beneficiary_record(auth_flow_dict, "FAIL", username, fhir_id, user_mbi_hash, user_hicn_hash, mesg)
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

        log_create_beneficiary_record(auth_flow_dict, "OK", username, fhir_id,
                                      user_mbi_hash, user_hicn_hash, "CREATE beneficiary record")
    return user


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
