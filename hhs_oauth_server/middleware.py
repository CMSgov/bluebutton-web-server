"""
Custom middleware for Blue Button 2.0.

SecurityHeadersMiddleware adds response headers that were previously
provided by the nginx reverse proxy. With the migration to Fargate
(gunicorn handles TLS directly), these headers are now set at the
application layer.
"""

import os

from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """ Adds Content-Security-Policy-Report-Only header (BB2-233).

    Other security headers (HSTS, X-Content-Type-Options, Referrer-Policy,
    X-Frame-Options) are handled by Django's SecurityMiddleware and
    XFrameOptionsMiddleware via settings in base_ec2.py.

    Args:
        MiddlewareMixin: Django legacy mixin class for pre 1.10 middleware
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        s3_domain = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "")
        s3_bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")

        if s3_domain:
            s3_origin = "https://{}/ ".format(s3_domain)
        elif s3_bucket:
            s3_origin = "https://s3.amazonaws.com/{}/ ".format(s3_bucket)
        else:
            s3_origin = ""

        self.csp_value = (
            "default-src 'self' {}".format(s3_origin)
            + "https://ajax.googleapis.com "
            + "https://stackpath.bootstrapcdn.com/bootstrap/ "
            + "https://unpkg.com/feather-icons "
            + "https://fonts.googleapis.com "
            + "https://fonts.gstatic.com"
        )

    def process_response(self, request, response):
        response["Content-Security-Policy-Report-Only"] = self.csp_value
        return response
