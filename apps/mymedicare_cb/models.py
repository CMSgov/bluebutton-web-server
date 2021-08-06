
import apps.logging.request_logger as logging

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from apps.fhir.server.authentication import match_fhir_id

from .authorization import OAuth2ConfigSLSx


class BBMyMedicareCallbackCrosswalkCreateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BBMyMedicareCallbackCrosswalkUpdateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def get_and_update_user(slsx_client: OAuth2ConfigSLSx, request=None):
    """
    Find or create the user associated
    with the identity information from the ID provider.

    Args:
        Identity parameters passed in from ID provider.
        slsx_client = OAuth2ConfigSLSx encapsulates all slsx exchanges and user info values as listed below:
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

    logger = logging.getLogger(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER, request)

    # Match a patient identifier via the backend FHIR server
    fhir_id, hash_lookup_type = match_fhir_id(
        mbi_hash=slsx_client.mbi_hash,
        hicn_hash=slsx_client.hicn_hash, request=request
    )

    log_dict = {
        "type": "mymedicare_cb:get_and_update_user",
        "subject": slsx_client.user_id,
        "fhir_id": fhir_id,
        "mbi_hash": slsx_client.mbi_hash,
        "hicn_hash": slsx_client.hicn_hash,
        "hash_lookup_type": hash_lookup_type,
        "crosswalk": {},
        "crosswalk_before": {},
    }

    # Init for types of crosswalk updates.
    hicn_updated = False
    mbi_updated = False
    mbi_updated_from_null = False

    try:
        # Does an existing user and crosswalk exist for SLSx username?
        user = User.objects.get(username=slsx_client.user_id)

        # fhir_id can not change for an existing user!
        if user.crosswalk.fhir_id != fhir_id:
            mesg = "Found user's fhir_id did not match"
            log_dict.update({
                "status": "FAIL",
                "user_id": user.id,
                "user_username": user.username,
                "mesg": mesg,
            })
            logger.info(log_dict)
            raise BBMyMedicareCallbackCrosswalkUpdateException(mesg)

        # Did the hicn change?
        if user.crosswalk.user_hicn_hash != slsx_client.hicn_hash:
            hicn_updated = True

        # Did the mbi change?
        if user.crosswalk.user_mbi_hash is not None:
            if user.crosswalk.user_mbi_hash != slsx_client.mbi_hash:
                mbi_updated = True
        else:
            # Did the mbi change from previously stored None/Null value?
            if slsx_client.mbi_hash is not None:
                mbi_updated = True
                mbi_updated_from_null = True

        # Update Crosswalk if there are any allowed changes or hash_type used for lookup changed.
        if user.crosswalk.user_id_type != hash_lookup_type or hicn_updated or mbi_updated:
            # Log crosswalk before state
            log_dict.update({
                "crosswalk_before": {
                    "id": user.crosswalk.id,
                    "user_hicn_hash": user.crosswalk.user_hicn_hash,
                    "user_mbi_hash": user.crosswalk.user_mbi_hash,
                    "fhir_id": user.crosswalk.fhir_id,
                    "user_id_type": user.crosswalk.user_id_type,
                },
            })

            with transaction.atomic():
                # Archive to audit crosswalk changes
                ArchivedCrosswalk.create(user.crosswalk)

                # Update crosswalk per changes
                user.crosswalk.user_id_type = hash_lookup_type
                user.crosswalk.user_hicn_hash = slsx_client.hicn_hash
                user.crosswalk.user_mbi_hash = slsx_client.mbi_hash
                user.crosswalk.save()

        # Beneficiary has been successfully matched!
        log_dict.update({
            "status": "OK",
            "user_id": user.id,
            "user_username": user.username,
            "hicn_updated": hicn_updated,
            "mbi_updated": mbi_updated,
            "mbi_updated_from_null": mbi_updated_from_null,
            "mesg": "RETURN existing beneficiary record",
            "crosswalk": {
                "id": user.crosswalk.id,
                "user_hicn_hash": user.crosswalk.user_hicn_hash,
                "user_mbi_hash": user.crosswalk.user_mbi_hash,
                "fhir_id": user.crosswalk.fhir_id,
                "user_id_type": user.crosswalk.user_id_type,
            },
        })
        logger.info(log_dict)

        return user, "R"
    except User.DoesNotExist:
        pass

    user = create_beneficiary_record(slsx_client, fhir_id=fhir_id, user_id_type=hash_lookup_type, request=request)

    log_dict.update({
        "status": "OK",
        "user_id": user.id,
        "user_username": user.username,
        "hicn_updated": hicn_updated,
        "mbi_updated": mbi_updated,
        "mbi_updated_from_null": mbi_updated_from_null,
        "mesg": "CREATE beneficiary record",
        "crosswalk": {
            "id": user.crosswalk.id,
            "user_hicn_hash": user.crosswalk.user_hicn_hash,
            "user_mbi_hash": user.crosswalk.user_mbi_hash,
            "fhir_id": user.crosswalk.fhir_id,
            "user_id_type": user.crosswalk.user_id_type,
        },
    })
    logger.info(log_dict)

    return user, "C"


# TODO default empty strings to null, requires non-null constraints to be fixed
def create_beneficiary_record(slsx_client: OAuth2ConfigSLSx, fhir_id=None, user_id_type="H", request=None):

    logger = logging.getLogger(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER, request)

    log_dict = {
        "type": "mymedicare_cb:create_beneficiary_record",
        "username": slsx_client.user_id,
        "fhir_id": fhir_id,
        "user_mbi_hash": slsx_client.mbi_hash,
        "user_hicn_hash": slsx_client.hicn_hash,
        "crosswalk": {},
    }

    if slsx_client.user_id is None or slsx_client.user_id == "":
        mesg = "username can not be None or empty string"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if slsx_client.hicn_hash is None:
        mesg = "user_hicn_hash can not be None"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)
    else:
        if len(slsx_client.hicn_hash) != 64:
            mesg = "incorrect user HICN hash format"
            log_dict.update({
                "status": "FAIL",
                "mesg": mesg,
            })
            logger.info(log_dict)
            raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    # If mbi_hash is not NULL, perform length check.
    if slsx_client.mbi_hash is not None:
        if len(slsx_client.mbi_hash) != 64:
            mesg = "incorrect user MBI hash format"
            log_dict.update({
                "status": "FAIL",
                "mesg": mesg,
            })
            logger.info(log_dict)
            raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if fhir_id is None:
        mesg = "fhir_id can not be None"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if fhir_id == "":
        mesg = "fhir_id can not be an empty string"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise BBMyMedicareCallbackCrosswalkCreateException(mesg)

    if User.objects.filter(username=slsx_client.user_id).exists():
        mesg = "user already exists"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise ValidationError(mesg, slsx_client.user_id)

    if Crosswalk.objects.filter(_user_id_hash=slsx_client.hicn_hash).exists():
        mesg = "user_hicn_hash already exists"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise ValidationError(mesg, slsx_client.hicn_hash)

    # If mbi_hash is not NULL, perform check for duplicate
    if slsx_client.mbi_hash is not None:
        if Crosswalk.objects.filter(_user_mbi_hash=slsx_client.mbi_hash).exists():
            mesg = "user_mbi_hash already exists"
            log_dict.update({
                "status": "FAIL",
                "mesg": mesg,
            })
            logger.info(log_dict)
            raise ValidationError(mesg, slsx_client.hicn_hash)

    if fhir_id and Crosswalk.objects.filter(_fhir_id=fhir_id).exists():
        mesg = "fhir_id already exists"
        log_dict.update({
            "status": "FAIL",
            "mesg": mesg,
        })
        logger.info(log_dict)
        raise ValidationError(mesg, fhir_id)

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
            user_mbi_hash=slsx_client.mbi_hash,
            fhir_id=fhir_id,
            user_id_type=user_id_type,
        )

        # Extra user information
        # TODO: remove the idea of UserProfile
        UserProfile.objects.create(user=user, user_type="BEN")
        # TODO: magic strings are bad
        group = Group.objects.get(name="BlueButton")  # TODO: these do not need a group
        user.groups.add(group)

        log_dict.update({
            "status": "OK",
            "mesg": "CREATE beneficiary record",
            "crosswalk": {
                "id": cw.id,
                "user_hicn_hash": cw.user_hicn_hash,
                "user_mbi_hash": cw.user_mbi_hash,
                "fhir_id": cw.fhir_id,
                "user_id_type": cw.user_id_type,
            },
        })
        logger.info(log_dict)

    return user


class AnonUserState(models.Model):
    state = models.CharField(default="", max_length=64, db_index=True)
    next_uri = models.CharField(default="", max_length=512)

    def __str__(self):
        return "%s %s" % (self.state, self.next_uri)
