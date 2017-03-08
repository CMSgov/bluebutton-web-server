from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class FhirServer(models.Model):
    """
    Server URL at Profile level
    eg.
    https://fhir-server1.cmsblue.cms.gov/fhir/baseDstu2/
    https://fhir-server2.cmsblue.cms.gov/fhir/stu3/

    ID will be used as reference in CrossWalk
    """

    name = models.CharField(max_length=254,
                            verbose_name="Friendly Server Name")
    fhir_url = models.URLField(verbose_name="Full URL to FHIR API with "
                                            "terminating /")
    shard_by = models.CharField(max_length=80,
                                default='Patient',
                                verbose_name='Key Resource type')
    client_auth = models.BooleanField(default=False,
                                      help_text="Is Client Authentication Required?")
    # Certs and keys will be stored in files and folders under
    # FHIR_CLIENT_CERTSTORE (set in base.py)
    # default will be BASE_DIR + /../certstore
    cert_file = models.TextField(max_length=250,
                                 blank=True,
                                 null=True,
                                 help_text="Name of Client Certificate file")
    key_file = models.TextField(max_length=250,
                                blank=True,
                                null=True,
                                help_text="Name of Client Key file")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Crosswalk(models.Model):
    """
    HICN/BeneID to User to FHIR Source Crosswalk and back.
    Linked to User Account
    Use fhir_url_id for id
    use fhir for resource.identifier
    BlueButton Text is moved to file keyed on user.
    HICN and BeneID added
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    fhir_source = models.ForeignKey(FhirServer,
                                    blank=True,
                                    null=True)
    fhir_id = models.CharField(max_length=80,
                               blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    mb_user = models.CharField(max_length=250,
                               blank=True)
    hicn = models.CharField(max_length=11,
                            blank=True,
                            verbose_name="Member Number(HICN)")
    beneid = models.CharField(max_length=11,
                              blank=True,
                              verbose_name="Beneficiary Id")
    # bb_text = models.TextField(verbose_name="Blue Button Text File",
    #                            blank=True,
    #                            null=True,
    #                            help_text=_("The MyMedicare.gov Blue "
    #                                        "Button text file is "
    #                                        "stored here."))

    # mb_user = MyMedicare.gov user login name
    # fhir_id = Identifier used in the patient Profile URL
    # eg. /baseDstu2/Patient/{fhir_id}
    # This will allow us to construct a URL to make a call directly to
    # a record, rather than requiring a search
    # when combined with fhir_source
    # eg. https://fhir-server1.bluebutton.cms.gov/fhir/baseDstu2/
    # + Patient/{fhir_id}

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def get_fhir_patient_url(self):
        # Return the fhir server url and {Resource_name}/{id}
        full_url = self.fhir_source.fhir_url
        if full_url.endswith('/'):
            pass
        else:
            full_url += '/'
        if self.fhir_source.shard_by:
            full_url += self.fhir_source.shard_by + '/'

        full_url += self.fhir_id

        return full_url

    def get_fhir_resource_url(self, resource_type):
        # Return the fhir server url
        full_url = self.fhir_source.fhir_url
        if full_url.endswith('/'):
            pass
        else:
            full_url += '/'

        if resource_type:
            full_url += resource_type + '/'

        return full_url


class BlueButtonText(models.Model):
    """
    User account and BlueButton Text File
    Moved from CrossWalk for better efficiency.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    bb_content = models.TextField(verbose_name="Blue Button Text File",
                                  blank=True,
                                  null=True,
                                  help_text=_("The MyMedicare.gov Blue "
                                              "Button text file is "
                                              "stored here."))

    def __str__(self):
        return '%s %s:%s[more...%s chars]' % (self.user.first_name,
                                              self.user.last_name,
                                              self.bb_content[:30],
                                              len(self.bb_content))
