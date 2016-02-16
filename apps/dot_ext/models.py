from django.db import models
from django.core.urlresolvers import reverse
from oauth2_provider.models import AbstractApplication
from ..capabilities.models import ProtectedCapability

class Application(AbstractApplication):
    protected_capability   = models.ForeignKey(ProtectedCapability)
    jwt                    = models.TextField(max_length=10240, default="",
                                              blank=True)
    agree                  = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse('dote_detail', args=[str(self.id)])
    
