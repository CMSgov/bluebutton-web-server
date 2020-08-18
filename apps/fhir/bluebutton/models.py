import logging
from requests import Response
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import get_user_id_salt
from apps.fhir.server.settings import fhir_settings
from django.utils.crypto import pbkdf2
import binascii
from django.db.models import (CASCADE, Q)


logger = logging.getLogger('hhs_server.%s' % __name__)


# Real fhir_id Manager subclass
class RealCrosswalkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(~Q(_fhir_id__startswith='-') & ~Q(_fhir_id=''))


# Synthetic fhir_id Manager subclass
class SynthCrosswalkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(_fhir_id__startswith='-'))


def hash_id_value(hicn):
    """
    Hashes an MBI or HICN to match fhir server logic:
    Both currently use the same hash salt ENV values.
    https://github.com/CMSgov/beneficiary-fhir-data/blob/master/apps/bfd-pipeline/bfd-pipeline-rif-load/src/main/java/gov/cms/bfd/pipeline/rif/load/RifLoader.java#L665-L706
    """
    return binascii.hexlify(pbkdf2(hicn,
                            get_user_id_salt(),
                            settings.USER_ID_ITERATIONS)).decode("ascii")


def hash_hicn(hicn):
    assert hicn != "", "HICN cannot be the empty string"

    return hash_id_value(hicn)


def hash_mbi(mbi):
    assert mbi != "", "MBI cannot be the empty string"
    # NOTE: mbi value can be None here.
    if mbi is None:
        return None
    else:
        return hash_id_value(mbi)


class Crosswalk(models.Model):
    """
    (MBI or HICN)/BeneID to User to FHIR Source Crosswalk and back.
    Linked to User Account
    Use fhir_url_id for id
    use fhir for resource.identifier
    BlueButton Text is moved to file keyed on user.
    MBI, HICN and BeneID added
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE,)
    _fhir_id = models.CharField(max_length=80,
                                null=False,
                                unique=True,
                                default=None,
                                db_column="fhir_id",
                                db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)

    # This value is to be set to the type of lookup used MBI or HICN
    user_id_type = models.CharField(max_length=1,
                                    verbose_name="Hash ID type last used for FHIR_ID lookup",
                                    default=settings.USER_ID_TYPE_DEFAULT,
                                    choices=settings.USER_ID_TYPE_CHOICES)
    # This stores the HICN hash value.
    # TODO: Maybe rename this to _user_hicn_hash in future.
    #   Keeping the same to not break backwards migration compatibility.
    _user_id_hash = models.CharField(max_length=64,
                                     verbose_name="HASH of User HICN ID",
                                     unique=True,
                                     null=False,
                                     default=None,
                                     db_column="user_id_hash",
                                     db_index=True)
    # This stores the MBI hash value.
    #     Can be null for backwards migration compatibility.
    _user_mbi_hash = models.CharField(max_length=64,
                                      verbose_name="HASH of User MBI ID",
                                      unique=True,
                                      null=True,
                                      default=None,
                                      db_column="user_mbi_hash",
                                      db_index=True)

    objects = models.Manager()  # Default manager
    real_objects = RealCrosswalkManager()  # Real bene manager
    synth_objects = SynthCrosswalkManager()  # Synth bene manager

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    @property
    def fhir_source(self):
        return fhir_settings

    @property
    def fhir_id(self):
        return self._fhir_id

    @fhir_id.setter
    def fhir_id(self, value):
        if self._fhir_id:
            raise ValidationError("this value cannot be modified.")
        self._fhir_id = value

    @property
    def user_hicn_hash(self):
        return self._user_id_hash

    @property
    def user_mbi_hash(self):
        return self._user_mbi_hash

    @user_hicn_hash.setter
    def user_hicn_hash(self, value):
        if self.pk:
            raise ValidationError("this value cannot be modified.")
        if self._user_id_hash:
            raise ValidationError("this value cannot be modified.")
        self._user_id_hash = value

    @user_mbi_hash.setter
    def user_mbi_hash(self, value):
        # Can update ONLY if previous hash value was None/Null.
        if self.pk and self._user_mbi_hash is not None:
            raise ValidationError("this value cannot be modified.")
        if self._user_mbi_hash:
            raise ValidationError("this value cannot be modified.")
        self._user_mbi_hash = value

    def get_fhir_resource_url(self, resource_type):
        # Return the fhir server url
        full_url = self.fhir_source.fhir_url
        if full_url.endswith('/'):
            pass
        else:
            full_url += '/'
        if resource_type:
            full_url += resource_type + '/'
        return full_url


class Fhir_Response(Response):
    """
    Build a more consistent Response object
    requests.Response can be missing fields if an error is encountered
    The purpose of this object is to encapsulate request.Response
    and make sure the items needed further upstream are present.

    """

    def __init__(self, req_response=Response):
        self.backend_response = req_response
        if req_response is None:
            req_response = Response

        for k, v in req_response.__dict__.items():
            self.__dict__[k] = v

        extend_response = {"_response": req_response,
                           "_text": "",
                           "_json": "{}",
                           "_xml": "</>",
                           "_status_code": "",
                           "_call_url": "",
                           "_cx": Crosswalk,
                           "_result": "",
                           "_owner": "",
                           "encoding": "utf-8",
                           "_content": ""
                           }

        # Add extra fields to Response Object
        for k, v in extend_response.items():
            self.__dict__[k] = v


def check_crosswalks():
    synth_count = Crosswalk.synth_objects.count()
    real_count = Crosswalk.real_objects.count()
    return {
        "synthetic": synth_count,
        "real": real_count,
    }
