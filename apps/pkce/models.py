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
    challenge = models.CharField(max_length=255, default=None)
    challenge_method = models.CharField(max_length=255, default="S256")
