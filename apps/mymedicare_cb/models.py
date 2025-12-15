import apps.logging.request_logger as logging

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from apps.versions import Versions
from apps.fhir.bluebutton.exceptions import UpstreamServerException

from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from apps.fhir.server.authentication import match_fhir_id
from rest_framework.exceptions import NotFound
from apps.dot_ext.utils import get_api_version_number_from_url

from .authorization import OAuth2ConfigSLSx, MedicareCallbackExceptionType


MAX_HICN_HASH_LENGTH = 64
MAX_MBI_LENGTH = 11


class BBMyMedicareCallbackCrosswalkCreateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BBMyMedicareCallbackCrosswalkUpdateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def __get_and_update_user(mbi, user_id, hicn_hash, request, auth_type, slsx_client=None):
    """
    Find or create the user associated
    with the identity information from the ID provider.
    Args:
        mbi = corresponds to user_mbi column of the bluebutton_crosswalk table, used to populate or update that column
              during auth flow if SLS has a different value than the database
        user_id = corresponds to username column of the auth_user table. Used to try and retrieve the auth_user record.
                  If the user does not exist (first auth), a new one is created.
        hicn_hash = corresponds to user_id_hash column of the bluebutton_crosswalk table. Used in v2 flows but not v3
                    though it can't be nulled out in bluebutton_crosswalk or an IntegrityError is raised.
        request = request from caller to pass along for logging info.
        auth_type = This value is either refresh or initial_auth. Used for logging
        slsx_client = OAuth2ConfigSLSx encapsulates all slsx exchanges and user info values as listed below
                      though as part of BB2-4294, we are now passing those values as parameters to account
                      for refresh token flow:
            subject = ID provider's sub or username
            mbi = MBI from SLSx
            hicn_hash = Previously hashed hicn
            first_name
            last_name
            email
    Returns:
        The user that was existing or newly created
        crosswalk_type =  Type of crosswalk activity:
            'R' = Returned existing crosswalk record
            'C' = Created new crosswalk record
    Raises:
        KeyError: If an expected key is missing from user_info.
        KeyError: If response from fhir server is malformed.
        AssertionError: If a user is matched but not all identifiers match.
    """

    try:
        version = request.session['version']
    except KeyError:
        path_info = request.__dict__.get('path_info')
        version = get_api_version_number_from_url(path_info)
    logger = logging.getLogger(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER, request)

    if version == Versions.V3:
        hicn_hash = None

    # Always attempt to get fresh FHIR ids from the backend for supported versions
    # so that FHIR ids are refreshed on every token/refresh operation. If the
    # backend reports a problem (UpstreamServerException) for the requested
    # version, bubble that error. If the backend simply returns no match
    # (NotFound), treat that as no FHIR id available and continue.

    versioned_fhir_ids = {}
    hash_lookup_type = None
    for supported_version in Versions.latest_versions():
        match_fhir_id_result = match_fhir_id(
            mbi=slsx_client.mbi,
            hicn_hash=hicn_hash,
            request=request,
            version=supported_version,
        )

        # If we found a fhir_id for this version, store it
        print(f'match_fhir_id_result : {match_fhir_id_result}')
        if match_fhir_id_result.success:
            versioned_fhir_ids[supported_version] = match_fhir_id_result.fhir_id
        else:
            # If there is not a fhir_id found for the requested version, then we want to raise an exception
            if match_fhir_id_result.error_type == 'upstream':
                if supported_version == version:
                    raise UpstreamServerException(match_fhir_id_result.error)
            elif match_fhir_id_result.error_type == 'not_found':
                # Intuitively, this should be the main thing we'd care about and seems wrong
                # However, we previously were just only checking for upstream errors
                # It would be more preferable to actually raise a NotFound error here
                # but there are other unit tests that appear to fail and expect that this would fail silently
                # A future ticket should address this
                pass

    # The get is maybe now redundant since match_fhir_id will return None if not found
    # but I don't think this hurts to do
    bfd_fhir_id_v2 = versioned_fhir_ids.get(Versions.V2, None)
    bfd_fhir_id_v3 = versioned_fhir_ids.get(Versions.V3, None)

    log_dict = {
        'type': f'mymedicare_cb:get_and_update_user_{auth_type}',
        'subject': user_id,
        'fhir_id_v2': bfd_fhir_id_v2,
        'fhir_id_v3': bfd_fhir_id_v3,
        'hicn_hash': slsx_client.hicn_hash,
        'hash_lookup_type': match_fhir_id_result.lookup_type,
        'crosswalk': {},
        'crosswalk_before': {},
    }

    hicn_updated = False
    try:
        # Does an existing user and crosswalk exist for this username?
        user = User.objects.get(username=user_id)

        # Did the hicn change?
        if user.crosswalk.user_hicn_hash != hicn_hash:
            hicn_updated = True

        update_fhir_id = False
        if (
            user.crosswalk.fhir_id(Versions.V2) == ''
            or user.crosswalk.fhir_id(Versions.V3) == ''
            or user.crosswalk.fhir_id(Versions.V2) != bfd_fhir_id_v2
            or user.crosswalk.fhir_id(Versions.V3) != bfd_fhir_id_v3
        ):
            update_fhir_id = True

        # Update Crosswalk if the user_mbi is null, but we have an mbi value from SLSx or
        # if the saved user_mbi value is different than what SLSx has
        if (
            (user.crosswalk.user_mbi is None and slsx_client.mbi is not None)
            or (user.crosswalk.user_mbi is not None and user.crosswalk.user_mbi != slsx_client.mbi)
            or (user.crosswalk.user_id_type != match_fhir_id_result.lookup_type or hicn_updated)
            or update_fhir_id
        ):
            # Log crosswalk before state
            log_dict.update({
                'crosswalk_before': {
                    'id': user.crosswalk.id,
                    'user_hicn_hash': user.crosswalk.user_hicn_hash,
                    'fhir_id_v2': bfd_fhir_id_v2,
                    'fhir_id_v3': bfd_fhir_id_v3,
                    'user_id_type': user.crosswalk.user_id_type,
                },
            })

            with transaction.atomic():
                # Archive to audit crosswalk changes
                ArchivedCrosswalk.create(user.crosswalk)
                if update_fhir_id:
                    user.crosswalk.fhir_id_v2 = bfd_fhir_id_v2
                    user.crosswalk.fhir_id_v3 = bfd_fhir_id_v3
                # Update crosswalk per changes
                user.crosswalk.user_id_type = match_fhir_id_result.lookup_type
                user.crosswalk.user_hicn_hash = slsx_client.hicn_hash
                user.crosswalk.user_mbi = slsx_client.mbi
                user.crosswalk.save()

        # Beneficiary has been successfully matched!
        log_dict.update({
            'status': 'OK',
            'user_id': user.id,
            'user_username': user.username,
            'hicn_updated': hicn_updated,
            'mesg': 'RETURN existing beneficiary record',
            'crosswalk': {
                'id': user.crosswalk.id,
                'user_hicn_hash': user.crosswalk.user_hicn_hash,
                'fhir_id_v2': bfd_fhir_id_v2,
                'fhir_id_v3': bfd_fhir_id_v3,
                'user_id_type': user.crosswalk.user_id_type,
            },
        })
        logger.info(log_dict)

        return user, 'R'
    except User.DoesNotExist:
        pass

    user = create_beneficiary_record(
        slsx_client,
        fhir_id_v2=bfd_fhir_id_v2,
        fhir_id_v3=bfd_fhir_id_v3,
        user_id_type=match_fhir_id_result.lookup_type,
        request=request
    )

    log_dict.update({
        'status': 'OK',
        'user_id': user.id,
        'user_username': user.username,
        'hicn_updated': hicn_updated,
        'mesg': 'CREATE beneficiary record',
        'crosswalk': {
            'id': user.crosswalk.id,
            'user_hicn_hash': user.crosswalk.user_hicn_hash,
            'fhir_id_v2': bfd_fhir_id_v2,
            'fhir_id_v3': bfd_fhir_id_v3,
            'user_id_type': user.crosswalk.user_id_type,
        },
    })
    logger.info(log_dict)

    return user, 'C'


def get_and_update_from_refresh(mbi, user_id, hicn_hash, request):
    return __get_and_update_user(
        mbi,
        user_id,
        hicn_hash,
        request,
        'refresh'
    )


def get_and_update_user_from_initial_auth(slsx_client: OAuth2ConfigSLSx, request):
    return __get_and_update_user(
        slsx_client.mbi,
        slsx_client.user_id,
        slsx_client.hicn_hash,
        request,
        'initial_auth',
        slsx_client=slsx_client
    )


def create_beneficiary_record(slsx_client: OAuth2ConfigSLSx,
                              fhir_id_v2=None, fhir_id_v3=None,
                              user_id_type='H', request=None) -> User:
    """function that takes meta information and creates a User, Crosswalk, and UserProfile

    Args:
        slsx_client (OAuth2ConfigSLSx): slsx client
        fhir_id_v2 (str, optional): fhir id for BFD v1/v2. Defaults to None.
        fhir_id_v3 (str, optional): fhir id for BFD v3. Defaults to None.
        user_id_type (str, optional): describes the lookup method that found this user_id. Defaults to 'H'.
        request (HttpRequest, optional): request object from upstream Django. Defaults to None.

    Returns:
        User: the User object that we created
    """
    logger = logging.getLogger(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER, request)

    log_dict = {
        'type': 'mymedicare_cb:create_beneficiary_record',
        'username': slsx_client.user_id,
        'fhir_id_v2': fhir_id_v2,
        'fhir_id_v3': fhir_id_v3,
        'user_hicn_hash': slsx_client.hicn_hash,
        'crosswalk': {},
    }

    _validate_asserts(logger, log_dict, [
        (slsx_client.user_id is None or slsx_client.user_id == '',
         'username can not be None or empty string',
         MedicareCallbackExceptionType.CALLBACK_CW_CREATE),
        (slsx_client.hicn_hash is None,
         'user_hicn_hash can not be None',
         MedicareCallbackExceptionType.CALLBACK_CW_CREATE),
        (slsx_client.hicn_hash is not None and len(slsx_client.hicn_hash) != MAX_HICN_HASH_LENGTH,
         'incorrect user HICN hash format',
         MedicareCallbackExceptionType.CALLBACK_CW_CREATE),
        (slsx_client.mbi is not None and len(slsx_client.mbi) != MAX_MBI_LENGTH,
         'incorrect user MBI format',
         MedicareCallbackExceptionType.CALLBACK_CW_CREATE),
        (User.objects.filter(username=slsx_client.user_id).exists(),
         'user already exists',
         MedicareCallbackExceptionType.VALIDATION_ERROR, slsx_client.user_id),
        (Crosswalk.objects.filter(_user_id_hash=slsx_client.hicn_hash).exists(),
         'user_hicn_hash already exists',
         MedicareCallbackExceptionType.VALIDATION_ERROR, slsx_client.hicn_hash),
        (slsx_client.mbi is not None and Crosswalk.objects.filter(_user_mbi=slsx_client.mbi).exists(),
         'user_mbi already exists',
         MedicareCallbackExceptionType.VALIDATION_ERROR, slsx_client.mbi),
        (fhir_id_v2 and Crosswalk.objects.filter(fhir_id_v2=fhir_id_v2).exists(),
         'fhir_id_v2 already exists', MedicareCallbackExceptionType.VALIDATION_ERROR, fhir_id_v2),
        (fhir_id_v2 == '', 'fhir_id_v2 can not be an empty string', MedicareCallbackExceptionType.CALLBACK_CW_CREATE, fhir_id_v2),
        (fhir_id_v3 and Crosswalk.objects.filter(fhir_id_v3=fhir_id_v3).exists(),
         'fhir_id_v3 already exists',
         MedicareCallbackExceptionType.VALIDATION_ERROR, fhir_id_v3),
        (fhir_id_v3 == '', 'fhir_id_v3 can not be an empty string', MedicareCallbackExceptionType.CALLBACK_CW_CREATE, fhir_id_v3),
        (fhir_id_v2 is None and fhir_id_v3 is None, 'a crosswalk must contain at least one valid fhir_id',
         MedicareCallbackExceptionType.CALLBACK_CW_CREATE, fhir_id_v2, fhir_id_v3)
    ])

    with transaction.atomic():
        user = User(username=slsx_client.user_id,
                    first_name=slsx_client.firstname,
                    last_name=slsx_client.lastname,
                    email=slsx_client.email)
        user.set_unusable_password()
        user.save()
        cw = Crosswalk.objects.create(
            user=user,
            user_hicn_hash=slsx_client.hicn_hash,
            user_mbi=slsx_client.mbi,
            fhir_id_v2=fhir_id_v2,
            fhir_id_v3=fhir_id_v3,
            user_id_type=user_id_type,
        )

        # Extra user information
        # TODO: remove the idea of UserProfile
        UserProfile.objects.create(user=user, user_type='BEN')
        # TODO: magic strings are bad
        group = Group.objects.get(name='BlueButton')  # TODO: these do not need a group
        user.groups.add(group)

        log_dict.update({
            'status': 'OK',
            'mesg': 'CREATE beneficiary record',
            'crosswalk': {
                'id': cw.id,
                'user_hicn_hash': cw.user_hicn_hash,
                'fhir_id_v2': cw.fhir_id(Versions.V2),
                'fhir_id_v3': cw.fhir_id(Versions.V3),
                'user_id_type': cw.user_id_type,
            },
        })
        logger.info(log_dict)

    return user


def _validate_asserts(logger, log_dict, asserts):
    """Asserts a list of tuples, iterating through, logging error messages and raising exceptions

    Args:
        logger (_type_): the logger
        log_dict (_type_): the log dictionary to update
        asserts (list : (boolean, string, enum)): the list of tuples to evaluate, t[0] is a boolean expression, t[1] is the error
                                                  message to log, and t[2] is the enum of exception to raise

    Raises:
        err: the error based on the result of iterating over asserts
    """

    for t in asserts:
        bexp = t[0]
        mesg = t[1]
        err_enum = t[2]
        if bexp:
            log_dict.update({'status': 'FAIL', 'mesg': mesg})
            logger.info(log_dict)
            err = None
            if err_enum == MedicareCallbackExceptionType.CALLBACK_CW_CREATE:
                err = BBMyMedicareCallbackCrosswalkCreateException(mesg)
            elif err_enum == MedicareCallbackExceptionType.CALLBACK_CW_UPDATE:
                err = BBMyMedicareCallbackCrosswalkUpdateException(mesg)
            elif err_enum == MedicareCallbackExceptionType.VALIDATION_ERROR:
                err = ValidationError(mesg, t[3:])
            else:
                err = Exception('Unkown medicare callback crosswalk exception type: {}'.format(err_enum))
            raise err


class AnonUserState(models.Model):
    state = models.CharField(default='', max_length=64, db_index=True)
    next_uri = models.CharField(default='', max_length=512)

    def __str__(self):
        return '%s %s' % (self.state, self.next_uri)
