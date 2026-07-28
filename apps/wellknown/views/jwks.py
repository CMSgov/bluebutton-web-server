import json
import os

from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


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
    public_pem = os.getenv('JWKS_PUBLIC_KEY_PEM', None).strip()
    if not public_pem:
        raise Http404()
    public_pem_json = json.loads(public_pem)

    return JsonResponse(public_pem_json)
