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
    # TODO spec
    challenge = models.CharField(max_length=255, default=None)
    # TODO spec
    challenge_method = models.CharField(max_length=255, default="S256")
