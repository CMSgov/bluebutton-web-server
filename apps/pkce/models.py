from django.db import models
from apps.pkce.constants import GRANT_MODEL


class CodeChallenge(models.Model):
    grant = models.OneToOneField(
        GRANT_MODEL,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    # up to 128 characters in plain transformation method, and
    # shorter if S256
    # https://datatracker.ietf.org/doc/html/rfc7636#section-4.2
    challenge = models.CharField(max_length=128, default=None)

    # TODO enum?
    # either "S256" or "plain" by spec
    # https://datatracker.ietf.org/doc/html/rfc7636#section-4.3
    challenge_method = models.CharField(max_length=5, default="S256", choices=["S256", "plain"])
