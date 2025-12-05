import binascii

from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CASCADE, Q
from django.utils.crypto import pbkdf2
from requests import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from django.core.validators import MinLengthValidator
from apps.accounts.models import get_user_id_salt

from apps.versions import Versions, VersionNotMatched


class BBFhirBluebuttonModelException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# Real fhir_id Manager subclass
class RealCrosswalkManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                ~Q(fhir_id_v2__startswith='-')
                & ~Q(fhir_id_v2='')
                & ~Q(fhir_id_v2__isnull=True)
                & ~Q(fhir_id_v3__startswith='-')
                & ~Q(fhir_id_v3='')
                & ~Q(fhir_id_v3__isnull=True)
            )
        )


# Synthetic fhir_id Manager subclass
class SynthCrosswalkManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(fhir_id_v2__startswith='-')
                | Q(fhir_id_v3__startswith='-')
            )
        )


def hash_id_value(hicn):
    """
    Hashes an MBI or HICN to match fhir server logic:
    Both currently use the same hash salt ENV values.
    https://github.com/CMSgov/beneficiary-fhir-data/blob/master/apps/bfd-pipeline/bfd-pipeline-rif-load/src/main/java/gov/cms/bfd/pipeline/rif/load/RifLoader.java#L665-L706
    """
    return binascii.hexlify(
        pbkdf2(hicn, get_user_id_salt(), settings.USER_ID_ITERATIONS)
    ).decode('ascii')


def hash_hicn(hicn):
    # BB2-237: Replaces ASSERT with exception. We should never reach this condition.
    if hicn == '':
        raise BBFhirBluebuttonModelException('HICN cannot be the empty string')

    return hash_id_value(hicn)


class Crosswalk(models.Model):
    """Represents a crosswalk between a Django user (auth_user) and their MBI/HICN/FHIR IDs

    Attributes:
        user: auth_user.id
        fhir_id_v2: v1/v2 BFD fhir patient id
        fhir_id_v3: v3 BFD fhir patient id
        date_created: date that record was created
        user_id_type: value is to be set to the type of lookup used MBI or HICN, TODO remove during BB2-3143
        _user_id_hash: HICN hash value, TODO remove during BB2-3143
        _user_mbi_hash: MBI hash value
        _user_mbi: unhashed MBI value

    Methods:
        fhir_id (version): returns the fhir_id for the specified BFD version
        set_fhir_id (value, version): sets the fhir_id for the specified BFD version

    Managers:
        objects: default manager
        real_objects: manager for real bene crosswalks
        synth_objects: manager for synthetic bene crosswalks
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
    )
    fhir_id_v2 = models.CharField(
        max_length=80,
        null=True,
        unique=True,
        db_column='fhir_id_v2',
        db_index=True,
        validators=[MinLengthValidator(1)],
    )
    fhir_id_v3 = models.CharField(
        max_length=80,
        null=True,
        unique=True,
        db_column='fhir_id_v3',
        db_index=True,
        validators=[MinLengthValidator(1)],
    )
    date_created = models.DateTimeField(auto_now_add=True)
    user_id_type = models.CharField(
        max_length=1,
        verbose_name='Hash ID type last used for FHIR_ID lookup',
        default=settings.USER_ID_TYPE_DEFAULT,
        choices=settings.USER_ID_TYPE_CHOICES,
    )
    _user_id_hash = models.CharField(
        max_length=64,
        verbose_name='HASH of User HICN ID',
        unique=True,
        null=False,
        default=None,
        db_column='user_id_hash',
        db_index=True,
    )
    _user_mbi_hash = models.CharField(
        max_length=64,
        verbose_name='HASH of User MBI ID',
        unique=True,
        null=True,
        default=None,
        db_column='user_mbi_hash',
        db_index=True,
    )
    _user_mbi = models.CharField(
        max_length=11,
        verbose_name='Unhashed MBI',
        null=True,
        default=None,
        db_column='user_mbi',
        db_index=True,
    )

    # TODO - This field is a legacy field, to be removed before migration bluebutton 0010
    _fhir_id = models.CharField(
        db_column='fhir_id',
        db_index=True,
        default=None,
        max_length=80,
        unique=True,
        null=True
    )

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(fhir_id_v2__isnull=False) | Q(fhir_id_v3__isnull=False),
                name='at_least_one_fhir_id_required'
            )
        ]

    def fhir_id(self, version: int = Versions.V2) -> str:
        """Helper method to return fhir_id based on BFD version, preferred over direct access"""
        if version in [Versions.V1, Versions.V2]:
            if self.fhir_id_v2 is not None and self.fhir_id_v2 != '':
                # TODO - This is legacy code, to be removed before migration bluebutton 0010
                # If fhir_id is empty, try to populate it from fhir_id_v2 to support old code
                self._fhir_id = self.fhir_id_v2
                self.save()
                return self.fhir_id_v2
            # TODO - This is legacy code, to be removed before migration bluebutton 0010
            # If fhir_id_v2 is empty, try to populate it from _fhir_id to support new code
            if self._fhir_id is not None and self._fhir_id != '':
                self.fhir_id_v2 = self._fhir_id
                self.save()
                return self._fhir_id
            return ''
        elif version == Versions.V3:
            if self.fhir_id_v3 is not None and self.fhir_id_v3 != '':
                return self.fhir_id_v3
            return ''
        else:
            raise ValidationError(f'{version} is not a valid BFD version')

    # THIS DOES NOT SAVE THE MODEL - CALLER MUST SAVE()
    def set_fhir_id(self, value, version: int = 2) -> None:
        """Helper method to set fhir_id based on BFD version, preferred over direct access"""
        if value == '':
            raise ValidationError('fhir_id can not be an empty string')
        if version in (1, 2):
            self.fhir_id_v2 = value
            # TODO - This is legacy code, to be removed in the future
            self._fhir_id = value
        elif version == 3:
            self.fhir_id_v3 = value
        else:
            raise VersionNotMatched(f'{version} is not a valid BFD version')

    @property
    def user_hicn_hash(self):
        return self._user_id_hash

    @property
    def user_mbi_hash(self):
        return self._user_mbi_hash

    @property
    def user_mbi(self):
        return self._user_mbi

    @user_hicn_hash.setter
    def user_hicn_hash(self, value):
        self._user_id_hash = value

    @user_mbi_hash.setter
    def user_mbi_hash(self, value):
        self._user_mbi_hash = value

    @user_mbi.setter
    def user_mbi(self, value):
        self._user_mbi = value

    objects = models.Manager()
    real_objects = RealCrosswalkManager()
    synth_objects = SynthCrosswalkManager()


class ArchivedCrosswalk(models.Model):
    """
    This model is used to keep an audit copy of a Crosswalk record's
    previous values when there are changes to the original.

    This is performed via code in the '_get_and_update_user()' function
    in apps/mymedicare_cb/models.py
    Attributes:
        user: auth_user.id
        fhir_id_v2: v1/v2 BFD fhir patient id
        fhir_id_v3: v3 BFD fhir patient id
        user_id_type: value is to be set to the type of lookup used MBI or HICN, TODO remove during BB2-3143
        _user_id_hash: HICN hash value, TODO remove during BB2-3143
        _user_mbi_hash: MBI hash value
        _user_mbi: unhashed MBI value
        date_created: date that record was created
        archived_at: date that record was archived
    Methods:
        create (crosswalk): static method to create an ArchivedCrosswalk from a Crosswalk instance
    """

    username = models.CharField(
        max_length=150,
        null=False,
        unique=False,
        default=None,
        db_column='username',
        db_index=True,
    )
    fhir_id_v2 = models.CharField(
        max_length=80,
        null=True,
        unique=False,
        db_column='fhir_id_v2',
        db_index=True,
    )
    fhir_id_v3 = models.CharField(
        max_length=80,
        null=True,
        unique=False,
        db_column='fhir_id_v3',
        db_index=True,
    )
    user_id_type = models.CharField(
        max_length=1,
        verbose_name='Hash ID type last used for FHIR_ID lookup',
        default=settings.USER_ID_TYPE_DEFAULT,
        choices=settings.USER_ID_TYPE_CHOICES,
    )
    _user_id_hash = models.CharField(
        max_length=64,
        verbose_name='HASH of User HICN ID',
        unique=False,
        null=False,
        default=None,
        db_column='user_id_hash',
        db_index=True,
    )
    _user_mbi_hash = models.CharField(
        max_length=64,
        verbose_name='HASH of User MBI ID',
        unique=False,
        null=True,
        default=None,
        db_column='user_mbi_hash',
        db_index=True,
    )
    _user_mbi = models.CharField(
        max_length=11,
        verbose_name='Unhashed MBI',
        null=True,
        default=None,
        db_column='user_mbi',
        db_index=True,
    )
    date_created = models.DateTimeField()
    archived_at = models.DateTimeField(auto_now_add=True)

    # TODO - This field is a legacy field, to be removed before migration bluebutton 0010
    _fhir_id = models.CharField(
        db_column='fhir_id',
        db_index=True,
        default=None,
        max_length=80,
        unique=False,
        null=True
    )

    @staticmethod
    def create(crosswalk):
        acw = ArchivedCrosswalk.objects.create(
            username=crosswalk.user.username,
            # TODO - This field is a legacy field, to be removed before migration bluebutton 0010
            _fhir_id=crosswalk._fhir_id,
            fhir_id_v2=crosswalk.fhir_id(2),
            fhir_id_v3=crosswalk.fhir_id(3),
            user_id_type=crosswalk.user_id_type,
            _user_id_hash=crosswalk.user_hicn_hash,
            _user_mbi=crosswalk._user_mbi,
            date_created=crosswalk.date_created,
        )
        acw.save()
        return acw


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

        extend_response = {
            '_response': req_response,
            '_text': '',
            '_json': '{}',
            '_xml': '</>',
            '_status_code': '',
            '_call_url': '',
            '_cx': Crosswalk,
            '_result': '',
            '_owner': '',
            'encoding': 'utf-8',
            '_content': '',
        }

        # Add extra fields to Response Object
        for k, v in extend_response.items():
            self.__dict__[k] = v


def get_crosswalk_bene_counts():
    """
    Get the crosswalk counts for real/synth benes
    """
    # Init counts dict
    counts_returned = {}

    start_time = datetime.utcnow().timestamp()

    # Get total table counts
    counts_returned['total'] = Crosswalk.objects.count()
    counts_returned['archived_total'] = ArchivedCrosswalk.objects.count()

    counts_returned['synthetic'] = Crosswalk.synth_objects.count()
    counts_returned['real'] = Crosswalk.real_objects.count()

    counts_returned['elapsed'] = round(datetime.utcnow().timestamp() - start_time, 3)

    return counts_returned
