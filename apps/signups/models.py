from django.db import models
from django.utils.encoding import python_2_unicode_compatible
# Create your models here.


@python_2_unicode_compatible
class CertifyingBody(models.Model):
   
    iss               = models.CharField(max_length=512, default="", verbose_name="Issuer",
                               help_text= "Must contain a QDN", unique=True)
    verified          = models.BooleanField(default=False, blank=True)
    email             = models.EmailField(max_length=256, default="")
    title             = models.CharField(max_length=256, default="", blank=True)
    website_url       = models.CharField(max_length=512, default="", blank=True)
    public_cert_url   = models.CharField(max_length=512, default="", blank=True,
                            verbose_name="Public Certificate URL",
                            help_text= "A link to the public cert corresponding to the private certificate used to sign software statements.")
    first_name        = models.CharField(max_length=512, default="", blank=True)
    last_name         = models.CharField(max_length=512, default="", blank=True)
    organization_name = models.CharField(max_length=512, default="", blank=True)
    notes             = models.TextField(max_length=512, default="", blank=True)
    created           = models.DateField(auto_now_add=True)
    updated           = models.DateField(auto_now=True)

    def __str__(self):
        return self.iss
        
    class Meta:     
        verbose_name_plural = "Certifying Bodies"
        