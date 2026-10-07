import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from os import path as ospath
from typing import Any

import jwt
import waffle
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.meta import Meta
from fhir.resources.R4B.parameters import Parameters, ParametersParameter
from fhir.resources.R4B.patient import Patient
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.validators import URIValidator, urlsplit
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError

from apps.constants import (
    CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS,
    HHS_SERVER_LOGNAME_FMT,
)
from apps.dot_ext.constants import (
    ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS,
    CAN_REQUIRED_CLAIM_FIELDS,
    CC_SYSTEM_CODING_SYSTEM,
    CC_SYSTEM_SOCIAL_SECURITY_NUMBER,
    CSP_IAL_ACCEPTED_JWT_ALGORITHMS,
    ID_ME_URL_CONTAINS,
    IDME_HIGHER_ISS,
    IDME_LOWER_ISS,
    PARAMETERS_ID_MATCH_META,
    PATIENT_ID_MATCH_META,
    URL_REGEX,
    YYYY_MM_DD_REGEX,
)
from apps.dot_ext.parser import normalize_address
from apps.dot_ext.utils import build_jwks_urls, validate_latin_extended_string
from apps.testclient.utils import _start_url_with_http_or_https

log = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


class RedirectURIValidator(URIValidator):
    def __init__(self, allowed_schemes):
        self.allowed_schemes = allowed_schemes

    def __call__(self, value):
        super(RedirectURIValidator, self).__call__(value)
        value = force_str(value)
        if len(value.split('#')) > 1:
            raise ValidationError('Redirect URIs must not contain fragments')
        scheme, netloc, path, query, fragment = urlsplit(value)

        if scheme.lower() not in self.allowed_schemes:
            raise ValidationError(
                'Invalid Redirect URI scheme: %s, Must be one of %s' % (scheme.lower(), self.allowed_schemes)
            )


def validate_uris(value):
    """
    This validator ensures that `value` contains valid blank-separated URIs"
    """
    v = RedirectURIValidator(oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES)
    for uri in value.split():
        v(uri)


def validate_url(value: str):
    """Validate that the value is a syntactically valid URL."""
    if not value:
        return
    value = value.strip()
    if not URL_REGEX.match(value):
        raise ValidationError('Enter a valid URL')


# Validate that there are no HTML tags
def validate_notags(value):
    if value != strip_tags(value):
        raise ValidationError(_('The text contains HTML tags. Please use plain-text only!'))


# Validate the application logo imagefield in form clean
def validate_logo_image(value):
    file_extension = ospath.splitext(value.name)[1]
    if file_extension.lower() not in ['.jpg', '.jpeg', '.png']:
        raise ValidationError('The file type must be JPEG, JPG, or PNG with a .jpg, .jpeg, or .png file extension!')

    if value.size > int(settings.APP_LOGO_SIZE_MAX) * 1024:
        raise ValidationError(
            'Max file size is %sKB. Your file size is %0.1fKB' % (str(settings.APP_LOGO_SIZE_MAX), value.size / 1024)
        )

    if value.image.width > int(settings.APP_LOGO_WIDTH_MAX):
        raise ValidationError(
            'Max image width is %s. Your image width is %s.'
            % (str(settings.APP_LOGO_WIDTH_MAX), str(value.image.width))
        )

    if value.image.height > int(settings.APP_LOGO_HEIGHT_MAX):
        raise ValidationError(
            'Max image height is %s. Your image height is %s.'
            % (str(settings.APP_LOGO_HEIGHT_MAX), str(value.image.height))
        )


class BaseTokenValidator(ABC):
    @abstractmethod
    def get_required_fields(self) -> list[str]:
        pass

    @abstractmethod
    def get_waffle_switch(self) -> str:
        pass

    @abstractmethod
    def authenticate_and_validate_token(self, token: str, client_id: str, jwks_client: jwt.PyJWKClient) -> dict:
        pass

    def _decode_and_validate_token(self, token: str, client_id: str, jwks_client: jwt.PyJWKClient) -> dict:
        """
        Validates and decodes a JWT token using the provided JWKS client. Used in client_credentials flow for CAN tokens
        and asymmetric auth flow.

        Args:
            token (str): The JWT token to validate and decode.
            client_id (str): The client ID to validate against the token's issuer and subject.
            jwks_client (jwt.PyJWKClient): The JWKS client to fetch the signing key.
            required_fields (list[str]): The list of required fields to validate in the JWT payload.

        Raises:
            InvalidRequestError: If the token is invalid or any validation checks fail.

        Returns:
            dict: The decoded JWT payload.
        """
        waffle_switch = self.get_waffle_switch()
        if waffle.switch_is_active(waffle_switch):
            required_fields = self.get_required_fields()
            signing_key = jwks_client.get_signing_key_from_jwt(token)  # type: ignore
            # pyjwt handles:
            # header - alg, kid
            # payload - iss, aud, exp
            host = _start_url_with_http_or_https(settings.HOSTNAME_URL)
            try:
                # NOTE: This function also handles subject and issuer validation matching the provided client_id
                data = jwt.decode_complete(
                    token,
                    signing_key,
                    issuer=client_id,
                    subject=client_id,
                    audience=host + reverse('oauth2_provider_v3:token-v3'),
                    leeway=timedelta(minutes=1),
                    options={
                        'require': required_fields,
                    },
                    algorithms=CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS,
                )
            except jwt.PyJWTError as e:
                log.warning(f'jwt.decode_complete() failed because {type(e)}')
                log.warning(f'error was {e}')
                raise InvalidRequestError

            payload, header = data.get('payload'), data.get('header')

            if not payload or not header or header.get('typ') != 'JWT':
                log.warning('Malformed JWT')
                raise InvalidRequestError

            if not cache.add(f'{payload.get("iss")}-{payload.get("jti")}', 'sentinel', 300):
                log.warning('jti/iss combo replay')
                raise InvalidRequestError

            if payload.get('exp') - datetime.now(timezone.utc).timestamp() > 300:
                log.warning('JWT exp is longer than 5 minutes away')
                raise InvalidRequestError

        else:
            payload = jwt.decode(token, options={'verify_signature': False})

        return payload


class CMSAlignedNetworksValidator(BaseTokenValidator):
    def get_required_fields(self) -> list[str]:
        return CAN_REQUIRED_CLAIM_FIELDS

    def get_waffle_switch(self) -> str:
        return 'client_credentials_validation'

    def authenticate_and_validate_token(self, token: str, client_id: str, **kwargs) -> dict:
        """
        Authenticates and validates a client credentials token.

        Args:
            token (str): The client credentials JWT.
            client_id (str): The client ID of the application making the request.
            **kwargs: Additional keyword arguments, such as a PyJWKClient instance.

        Raises:
            InvalidRequestError: If any validation step fails.

        Returns:
            dict: The processed payload extracted from the IAL JWT.
        """
        payload = self._decode_and_validate_token(token, client_id, **kwargs)
        id_token = self._validate_smart_extension(payload)
        csp_jwks_url = self._get_csp_jwks_url(id_token)
        ial_valid = self._validate_ial_jwt(id_token, jwt.PyJWKClient(csp_jwks_url))
        processed_payload = self._parse_ial_into_parameter(ial_valid)
        return processed_payload

    def _validate_smart_extension(self, payload: dict) -> dict:
        """
        Validates the CMS Smart extension within the JWT payload and extracts the id_token.

        Args:
            payload (dict): The decoded JWT payload containing extensions.

        Raises:
            InvalidRequestError: If the CMS Smart extension is missing or malformed.

        Returns:
            dict: The extracted id_token from the CMS Smart extension.
        """
        waffle_switch = self.get_waffle_switch()
        if waffle.switch_is_active(waffle_switch):
            cms_smart = payload.get('extensions', {}).get('cms_smart')
            if not cms_smart:
                log.warning('No CMS_Smart extension')
                raise InvalidRequestError

            if (
                cms_smart.get('version') != '1'
                or cms_smart.get('purpose_of_use') != 'PATRQT'
                or not cms_smart.get('id_token')
            ):
                log.warning('Malformed CMS_Smart extension')
                raise InvalidRequestError

            id_token = cms_smart.get('id_token')

            return id_token
        else:
            return payload.get('extensions', {}).get('cms_smart', {}).get('id_token')

    def _validate_ial_jwt(self, id_token: str, jwks_client: jwt.PyJWKClient) -> dict:
        """Validates an IAL JWT from a trusted CSP

        Args:
            id_token (str): base64 encoded id_token jwt from cms_smart extension
            jwks_client (PyJWKClient): instantiated client for the authorization jwt

        Raises:
            InvalidRequestError: if any validation step fails, log and raise

        Returns:
            str: the decoded payload of the IAL JWT
        """
        waffle_switch = self.get_waffle_switch()
        if waffle.switch_is_active(waffle_switch):
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            try:
                data = jwt.decode_complete(
                    id_token,
                    signing_key,
                    # leeway=timedelta(minutes=5),
                    options={
                        'require': [
                            'iss',
                            'sub',
                            'aud',
                            'jti',
                            'exp',
                            'iat',
                            'identity_assurance_level',
                            'auth_time',
                            'family_name',
                            'given_name',
                            'birthdate',
                        ],
                        'verify_aud': False,
                    },
                    algorithms=CSP_IAL_ACCEPTED_JWT_ALGORITHMS,
                )
            except jwt.PyJWTError as e:
                log.warning(f'jwt.decode_complete() failed because {type(e)}')
                raise InvalidRequestError
            payload, header = data.get('payload'), data.get('header')

            if not payload or not header or header.get('typ') != 'JWT':
                log.warning('Malformed header / payload')
                raise InvalidRequestError

            # Validate iat and auth_time
            self._validate_time_comparison(payload, 'iat', 300)
            self._validate_time_comparison(payload, 'auth_time', 300)

            if not self._validate_idme_url_for_id_token_and_environment(payload.get('iss', '')):
                log.warning('The issuer of the token is not valid for this environment')
                raise InvalidRequestError

            if not cache.add(f'{payload.get("iss")}-{payload.get("jti")}', 'sentinel', 300):
                log.warning('jti/iss combo replay')
                raise InvalidRequestError

            if payload.get('identity_assurance_level') < 2:
                log.warning(f'identity_assurance_level was invalid: {payload.get("identity_assurance_level")}')
                raise InvalidRequestError

            if not validate_latin_extended_string(payload.get('family_name')):
                log.warning(
                    f'family_name is empty or has encoded characters greater than 383: {payload.get("family_name")}'
                )
                raise InvalidRequestError

            if not validate_latin_extended_string(payload.get('given_name')):
                log.warning(
                    f'given_name is empty or has encoded characters greater than 383: {payload.get("given_name")}'
                )
                raise InvalidRequestError

            if not re.match(YYYY_MM_DD_REGEX, payload.get('birthdate')):
                log.warning('birthdate was not a valid string')
                raise InvalidRequestError
        else:
            try:
                payload = jwt.decode(id_token, options={'verify_signature': False})
            except jwt.PyJWTError as e:
                log.warning(f'jwt.decode_complete() failed because {type(e)}')
                raise InvalidRequestError
            if not self._validate_idme_url_for_id_token_and_environment(payload.get('iss', '')):
                log.warning('The issuer of the token is not valid for this environment')
                raise InvalidRequestError

        return payload

    def _validate_time_comparison(
        self, payload_data: dict[str, Any], jwt_key: str, max_age_seconds: int
    ) -> bool | InvalidRequestError:
        """
        Validates if iat or auth_time:
         1. Are numbers
         2. Does not occur in the future
         3. Is within the required amount of time.

        Args:
            payload_data: The payload of the IAL JWT after being decoded
            jwt_key: The key to get the jwt timestamp from (iat or auth_time for now)
            max_age_seconds: The max time window/delta (in seconds) that the jwt_key is valid for

        Raises:
            InvalidRequestError: if any validation step fails, log and raise

        Returns:
            True if no InvalidRequestError's are raised
        """
        # Verify we get the correct type
        try:
            jwt_key_ts = float(payload_data.get(jwt_key))
        except (TypeError, ValueError):
            log.warning(f'{jwt_key} was not a numeric timestamp ({jwt_key})')
            raise InvalidRequestError

        current_ts = datetime.now(timezone.utc).timestamp()
        # Verify iat or auth_time isn't in the future
        if jwt_key_ts > current_ts:
            log.warning(f'JWT {jwt_key} is in the future ({jwt_key})')
            raise InvalidRequestError

        # Verify iat or auth_time isn't too old
        if current_ts - jwt_key_ts > max_age_seconds:
            log.warning(f'JWT {jwt_key} was older than {float(max_age_seconds / 60)} minutes ({jwt_key})')
            raise InvalidRequestError
        return True

    def _parse_ial_into_parameter(self, payload: dict) -> dict:
        """Parses an IAL token into a Patient and Parameters resource

        Args:
            payload (dict): the IAL token

        Returns:
            dict: a dictionary representing the Parameters object
        """
        patient_name = HumanName(
            use='official',
            family=payload.get('family_name'),
            given=[payload.get('given_name')],
        )

        telecoms = []
        if payload.get('phone_number') and payload.get('phone_number_verified'):
            telecoms.append(
                ContactPoint(
                    system='phone',
                    value=payload.get('phone_number'),
                    use='mobile',
                    rank=1,
                )
            )

        if payload.get('email'):
            telecoms.append(ContactPoint(system='email', value=payload.get('email'), use='home', rank=2))

        gender_map = {'f': 'female', 'm': 'male', 'o': 'other', 'u': 'unknown'}
        gender = payload.get('gender', 'u').lower()
        patient_gender = gender_map.get(gender[0], 'unknown')

        patient_birthdate = payload.get('birthdate')

        addresses = []
        if (home := payload.get('address')) and home.get('street_address'):
            street_address = home.get('street_address')

            parts = [
                street_address,
                home.get('locality', ''),
                home.get('region', ''),
                home.get('postal_code', ''),
            ]
            address_parts = ', '.join(part for part in parts if part)
            normalized_address = normalize_address(address_parts)

            if normalized_address:
                addresses.append(
                    Address(
                        use='home',
                        type='both',
                        text=normalized_address,
                        line=[normalized_address],
                        city=home.get('locality'),
                        state=home.get('region'),
                        postalCode=home.get('postal_code'),
                        country=home.get('country'),
                    )
                )

        for historical in payload.get('historical_address', []):
            if not (street_address := historical.get('street_address')):
                continue

            parts = [
                street_address,
                historical.get('locality', ''),
                historical.get('region', ''),
                historical.get('postal_code', ''),
            ]
            address_parts = ', '.join(part for part in parts if part)
            normalized_address = normalize_address(address_parts)

            if normalized_address:
                addresses.append(
                    Address(
                        use='old',
                        type='both',
                        text=normalized_address,
                        line=[normalized_address],
                        city=historical.get('locality'),
                        state=historical.get('region'),
                        postalCode=historical.get('postal_code'),
                        country=historical.get('country'),
                    )
                )

        identifiers = []
        if (ssn := payload.get('ssn_itin_short') or payload.get('SSN', '')[-4:]) and len(ssn) == 4:
            ssn_coding = Coding(
                system=CC_SYSTEM_CODING_SYSTEM,
                code='SS',
                display='Social Security Number',
            )
            ssn_type = CodeableConcept(coding=[ssn_coding])
            identifiers.append(
                Identifier(
                    use='official',
                    type=ssn_type,
                    system=CC_SYSTEM_SOCIAL_SECURITY_NUMBER,
                    value=ssn,
                )
            )

        patient_meta = Meta(profile=[PATIENT_ID_MATCH_META])

        patient = Patient(
            name=[patient_name],
            telecom=telecoms,
            gender=patient_gender,
            birthDate=patient_birthdate,
            address=addresses,
            identifier=identifiers,
            meta=patient_meta,
        )

        id_match_meta = Meta(profile=[PARAMETERS_ID_MATCH_META])

        id_match_payload = Parameters(
            id='IDIMatchInputParameters',
            meta=id_match_meta,
            parameter=[ParametersParameter(name='IDIPatient', resource=patient)],
        )

        return id_match_payload.model_dump(mode='json', exclude_none=True)

    def _get_csp_jwks_url(self, id_token: str) -> str:
        """Get the JSON Web Key Set (JWKS) URL for the given ID token.

        Args:
            id_token (str): The ID token to extract the issuer from.

        Returns:
            str: The JWKS URL corresponding to the issuer.

        Raises:
            InvalidRequestError: If the ID token does not have a valid issuer.
        """
        pre_verified_ial = jwt.decode(id_token, options={'verify_signature': False})
        url_map = build_jwks_urls()
        csp_jwks_url = url_map.get(pre_verified_ial.get('iss', ''))

        if not csp_jwks_url:
            log.warning('id_token did not have a valid iss')
            raise InvalidRequestError

        return csp_jwks_url

    def _validate_idme_url_for_id_token_and_environment(self, issuer: str) -> bool:
        """Determine if the issuer of the id_token is valid for the environment for ID.me client_credentials
        calls
        Args:
            issuer (str): Where the token was issued from
        Returns:
            bool: Whether or not the environment is valid for the id token issuer
        """

        # If the issue does not contain oidc, it is not ID.me, and it must be CLEAR
        # CLEAR does not differentiate between environments at this time
        if ID_ME_URL_CONTAINS not in issuer:
            return True

        env = os.environ.get('TARGET_ENV', 'local')
        # if the env is prod, and the issuer is not the prod url, return false
        # or if the env is not prod, and the issuer is not the lower env url, return false
        if (env == 'prod' and issuer != IDME_HIGHER_ISS) or (env != 'prod' and issuer != IDME_LOWER_ISS):
            log.warning(f'Invalid URL for env: {env}: {issuer}')
            return False

        return True


class AsymmetricAuthValidator(BaseTokenValidator):
    def get_waffle_switch(self) -> str:
        return 'asymmetric_auth_validation'

    def get_required_fields(self) -> list[str]:
        return ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS

    def _validate_jku(self, token: str, jwks_uri: str) -> None:
        """
        Validates the 'jku' (JSON Web Key URL) parameter against the expected jwks_uri.

        Args:
            token (str): the base64 encoded auth jwt
            jwks_uri (str): the expected JSON Web Key URL

        Raises:
            InvalidRequestError: if the 'jku' is not valid
        """
        waffle_switch = self.get_waffle_switch()
        if waffle.switch_is_active(waffle_switch):
            unverified_header = jwt.get_unverified_header(token)
            jku = unverified_header.get('jku')
            # Just return if not present since it's optional
            if not jku:
                return

            if jku != jwks_uri:
                log.warning('id_token did not have a valid jku')
                raise InvalidRequestError(
                    status_code=HTTPStatus.BAD_REQUEST,
                )
        else:
            return

    def authenticate_and_validate_token(self, token: str, client_id: str, **kwargs) -> dict:
        """
        Authenticates and validates the given token using the provided client ID and JWKS client.

        Args:
            token (str): the base64 encoded auth jwt
            client_id (str): the client ID to validate against
            jwks_client (jwt.PyJWKClient): the JWKS client to use for validation

        Returns:
            dict: the decoded and validated token payload

        Raises:
            InvalidRequestError: if the token is not valid
        """
        jwks_uri = kwargs.get('jwks_uri')
        self._validate_jku(token, jwks_uri)
        payload = self._decode_and_validate_token(token, client_id)
        return payload
