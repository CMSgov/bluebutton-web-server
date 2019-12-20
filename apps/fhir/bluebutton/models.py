import logging
from requests import Response
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import get_user_id_salt
from apps.fhir.server.models import ResourceRouter
from django.utils.crypto import pbkdf2
import binascii
from django.db.models import (CASCADE, Q)


logger = logging.getLogger('hhs_server.%s' % __name__)


# Real fhir_id Manager subclass
class RealCrosswalkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(~Q(fhir_id__startswith='-') & ~Q(fhir_id=''))


# Synthetic fhir_id Manager subclass
class SynthCrosswalkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(fhir_id__startswith='-'))


def hash_hicn(hicn):
    """
    Hashes a hicn to match fhir server logic:
    https://github.com/CMSgov/beneficiary-fhir-data/blob/master/apps/bfd-pipeline/bfd-pipeline-rif-load/src/main/java/gov/cms/bfd/pipeline/rif/load/RifLoader.java#L665-L706

    """
    assert hicn != "", "HICN cannot be the empty string"

    return binascii.hexlify(pbkdf2(hicn,
                            get_user_id_salt(),
                            settings.USER_ID_ITERATIONS)).decode("ascii")


class Crosswalk(models.Model):
    """
    HICN/BeneID to User to FHIR Source Crosswalk and back.
    Linked to User Account
    Use fhir_url_id for id
    use fhir for resource.identifier
    BlueButton Text is moved to file keyed on user.
    HICN and BeneID added
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE,)
    fhir_source = models.ForeignKey(ResourceRouter,
                                    on_delete=CASCADE,
                                    blank=True,
                                    null=True)
    # default=settings.FHIR_SERVER_DEFAULT)
    _fhir_id = models.CharField(max_length=80,
                                null=False,
				unique=True,
                                default=None,
                                db_column="fhir_id",
                                db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)

    user_id_type = models.CharField(max_length=1,
                                    default=settings.USER_ID_TYPE_DEFAULT,
                                    choices=settings.USER_ID_TYPE_CHOICES)
    _user_id_hash = models.CharField(max_length=64,
                                     verbose_name="PBKDF2 of User ID",
                                     unique=True,
                                     null=False,
                                     default=None,
                                     db_column="user_id_hash",
                                     db_index=True)

    objects = models.Manager()  # Default manager
    real_objects = RealCrosswalkManager()  # Real bene manager
    synth_objects = SynthCrosswalkManager()  # Synth bene manager

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    @property
    def fhir_id(self):
        return self._fhir_id

    @fhir_id.setter
    def fhir_id(self, value):
        if self._fhir_id:
            raise ValidationError("this value cannot be modified.")
        self._fhir_id = value

    @property
    def user_id_hash(self):
        return self._user_id_hash

    @user_id_hash.setter
    def user_id_hash(self, value):
        if self.pk:
            raise ValidationError("this value cannot be modified.")
        if self._user_id_hash:
            raise ValidationError("this value cannot be modified.")
        self._user_id_hash = value

    def set_hicn(self, hicn):
        if self.pk:
            raise ValidationError("this value cannot be modified.")
        self.user_id_hash = hash_hicn(hicn)

    def get_fhir_patient_url(self):
        # Return the fhir server url and {Resource_name}/{id}
        full_url = self.fhir_source.fhir_url
        if full_url.endswith('/'):
            pass
        else:
            full_url += '/'
        if self.fhir_source.shard_by:
            full_url += self.fhir_source.shard_by + '/'
        full_url += self.fhir_id
        return full_url

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
