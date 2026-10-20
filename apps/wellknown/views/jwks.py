import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

from apps.constants import AUTH_SIGNING_ALG_ES384, CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS


# the lru_cache is used so that the possible creation of RSA keypairs only happens once
@lru_cache(maxsize=1)
def _local_private_keys() -> tuple:
    """Return the ``(rsa_key, ec_key)`` private keys backing ``_local_jwks``.

    ``JWKS_PRIVATE_KEY_PEM`` (a PEM private key, RSA or P-384 EC) gives a developer a stable key
    for signing ``client_assertion`` JWTs; it is meant to be a unique ephemeral key that lives just
    for each time the containers are spun up.
    """
    pem = os.getenv('JWKS_PRIVATE_KEY_PEM', '').strip()
    loaded = load_pem_private_key(pem.encode('utf-8'), password=None) if pem else None

    if isinstance(loaded, rsa.RSAPrivateKey):
        rsa_key = loaded
    else:
        rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

    if isinstance(loaded, ec.EllipticCurvePrivateKey):
        ec_key = loaded
    else:
        ec_key = ec.generate_private_key(ec.SECP384R1())

    return rsa_key, ec_key


def _local_jwks() -> dict:
    """Build a public-only JWKS for local development, one key per accepted JWT algorithm."""
    rsa_key, ec_key = _local_private_keys()

    keys = []
    for alg in CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS:
        algorithm = ECAlgorithm if alg == AUTH_SIGNING_ALG_ES384 else RSAAlgorithm
        public_key = (ec_key if alg == AUTH_SIGNING_ALG_ES384 else rsa_key).public_key()
        jwk = algorithm.to_jwk(public_key, as_dict=True)
        jwk.update({'use': 'sig', 'alg': alg, 'kid': f'local-jwks-{alg.lower()}'})
        keys.append(jwk)
    return {'keys': keys}


@never_cache
@require_GET
def jwks_json(request):
    """Serve BB2's internal JWKS at ``/.well-known/jwks.json``.

    Publishes the public keys used to validate signed ``client_assertion`` JWTs against an
    application's registered ``jwks_uri``. Deployed environments supply the JWKS document via
    ``JWKS_PUBLIC_KEY_PEM``. In the ``local`` and ``codebuild`` environments, with that unset, a local
    development JWKS is served instead. Returns 404 otherwise.
    """
    public_pem = os.getenv('JWKS_PUBLIC_KEY_PEM', '').strip()
    if public_pem:
        return JsonResponse(json.loads(public_pem))

    if getattr(settings, 'TARGET_ENV', None) in ('local', 'codebuild'):
        return JsonResponse(_local_jwks())

    raise Http404()
