import logging
from requests import Response
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
# from django.utils.translation import ugettext_lazy as _
from apps.fhir.server.models import ResourceRouter
from django.utils.crypto import pbkdf2
import binascii

logger = logging.getLogger('hhs_server.%s' % __name__)


@python_2_unicode_compatible
class Crosswalk(models.Model):
    """
    HICN/BeneID to User to FHIR Source Crosswalk and back.
    Linked to User Account
    Use fhir_url_id for id
    use fhir for resource.identifier
    BlueButton Text is moved to file keyed on user.
    HICN and BeneID added
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    fhir_source = models.ForeignKey(ResourceRouter,
                                    blank=True,
                                    null=True)
    fhir_id = models.CharField(max_length=80,
                               blank=True, default="")
    date_created = models.DateTimeField(auto_now_add=True)

    user_id_type = models.CharField(max_length=1,
                                    default=settings.USER_ID_TYPE_DEFAULT,
                                    choices=settings.USER_ID_TYPE_CHOICES)
    user_id_hash = models.CharField(max_length=64,
                                    blank=True,
                                    default="",
                                    verbose_name="PBKDF2 of User ID")

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def encrypt_and_set_user_id_hash(self, plaintext_user_id):

        self.user_id_hash = binascii.hexlify(pbkdf2(plaintext_user_id,
                                                    settings.USERID_ENCRYPT_SALT,
                                                    settings.USERID_ENCRYPT_NUM_ITERS)).decode("ascii")
        return self.user_id_hash

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
            # logger.debug("Key:%s with Value:%s" % (k, v))
            self.__dict__[k] = v
