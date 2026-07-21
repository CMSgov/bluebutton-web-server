import json

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from jwt.algorithms import RSAAlgorithm


@never_cache
@require_GET
def jwks_json(request):
    """Serve BB2's internal JWKS at ``/.well-known/jwks.json``.

    Publishes the public half of the RSA keypair used to validate signed
    ``client_assertion`` JWTs against an application's registered ``jwks_uri``.
    The keypair is supplied per-environment via environment variables
    (``JWKS_PUBLIC_KEY_PEM`` / ``JWKS_PRIVATE_KEY_PEM``); this endpoint only needs
    the public key. Returns 404 when no public key is configured.
    """
    public_pem = (getattr(settings, 'JWKS_PUBLIC_KEY_PEM', 'viable-public-key') or '').strip()
    if not public_pem:
        raise Http404()

    public_key = load_pem_public_key(public_pem.encode('utf-8'))
    jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk.update({'kid': settings.JWKS_KEY_ID, 'use': 'sig', 'alg': 'RS256'})

    return JsonResponse({'keys': [jwk]})
