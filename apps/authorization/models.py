from django.db import models
from django.conf import settings
from oauth2_provider.settings import oauth2_settings


class DataAccessGrant(models.Model):
    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    application = models.ForeignKey(
        oauth2_settings.APPLICATION_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("beneficiary", "application")
        indexes = [
            models.Index(fields=["beneficiary", "application"]),
            models.Index(fields=["beneficiary"]),
            models.Index(fields=["application"]),
        ]
