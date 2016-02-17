from django.db import models
from django.core.urlresolvers import reverse
from oauth2_provider.models import AbstractApplication
from ..capabilities.models import ProtectedCapability
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Endorsement(models.Model):
    title   = models.TextField(max_length=256, default="")
    iss     = models.TextField(max_length=512, default="", verbose_name="Issuer",
                               help_text= "Must contain a QDN")
    jws     = models.TextField(max_length=10240, default="")

    def __str__(self):
        return self.title
    
class Application(AbstractApplication):
    scope                  = models.ManyToManyField(ProtectedCapability)
    endorsements           = models.ManyToManyField(Endorsement, blank=True, null=True)
    agree                  = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse('dote_detail', args=[str(self.id)])
    


    

    