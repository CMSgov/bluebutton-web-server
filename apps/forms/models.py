import uuid
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

INTERIM_PROD_ACCESS_FORM_TYPE = "interim-prod-access"
IN_PROGRESS_STATUS = "in-progress"
SUBMITTED_STATUS = "submitted"
REJECTED_STATUS = "rejected"


class Forms(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, db_index=True)
    form_data = JSONField()
    status = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
