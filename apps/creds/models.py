import uuid

from django.db import models
from oauth2_provider.settings import oauth2_settings


class ProdCredentialingReqest(models.Model):
    # 1 or more prod credentialing request can be generated for an app
    application = models.ForeignKey(oauth2_settings.APPLICATION_MODEL,
                                    on_delete=models.CASCADE,
                                    verbose_name="Application",
                                    help_text="Target application of a prod credentialing request")
    creds_request_id = models.UUIDField(primary_key=True,
                                        unique=True,
                                        default=uuid.uuid4,
                                        editable=False,
                                        verbose_name="Prod Credentialing Request ID",
                                        help_text="A UUID assigned to a prod credentialing request")
    date_created = models.DateTimeField(auto_now_add=True)
    date_fetched = models.DateTimeField(null=True, blank=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    visits_count = models.IntegerField(default=0)
