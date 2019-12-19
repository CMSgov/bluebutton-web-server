from django.db import models
from apps.fhir.server.utils import text_to_list, init_text_list
from django.db.models import CASCADE


class ResourceRouter(models.Model):
    """
    Server URL at Profile level
    eg.
    https://fhir-server1.cmsblue.cms.gov/fhir/baseDstu2/
    https://fhir-server2.cmsblue.cms.gov/fhir/stu3/

    ID will be used as reference in CrossWalk
    """

    name = models.CharField(max_length=254,
                            verbose_name="Friendly Server Name")
    server_address = models.URLField(verbose_name="Server Name in URL form")
    server_path = models.CharField(max_length=254,
                                   default="/",
                                   verbose_name="path to API with "
                                                "terminating /")
    server_release = models.CharField(max_length=254,
                                      default="v1/fhir/",
                                      verbose_name="FHIR release with "
                                                   "terminating /")
    server_search_expiry = models.IntegerField(verbose_name="Search expires "
                                                            "in seconds",
                                               default=1800)
    fhir_url = models.URLField(verbose_name="Full URL to FHIR API with "
                                            "terminating /")
    shard_by = models.CharField(max_length=80,
                                default='Patient',
                                verbose_name='Key Resource type')

    supported_resource = models.ManyToManyField('SupportedResourceType')

    client_auth = models.BooleanField(default=False,
                                      help_text="Is Client Authentication "
                                                "Required?")
    # Certs and keys will be stored in files and folders under
    # FHIR_CLIENT_CERTSTORE (set in base.py)
    # default will be BASE_DIR + /../certstore
    cert_file = models.TextField(max_length=250,
                                 blank=True,
                                 null=True,
                                 help_text="Client Certificate filename.")
    key_file = models.TextField(max_length=250,
                                blank=True,
                                null=True,
                                help_text="Name of Client Key filename")
    server_verify = models.BooleanField(default=False,
                                        help_text="Server Verify "
                                                  "(Default=False)")
    wait_time = models.IntegerField(default=30,
                                    null=False,
                                    blank=True,
                                    verbose_name="Server wait time (Seconds)",
                                    help_text="Seconds to wait before timing "
                                              "out a call to this server.")

    def __str__(self):
        return self.name

    def get_resources(self):
        rType = []
        for s in self.supported_resource.all():
            rType.append(s.resourceType)
        return rType

    def get_protected_resources(self):
        rProtectedType = []
        for s in self.supported_resource.all():
            if s.secure_access:
                rProtectedType.append(s.resourceType)
        return rProtectedType

    def get_open_resources(self):
        rOpenType = []
        for s in self.supported_resource.all():
            if not s.secure_access:
                rOpenType.append(s.resourceType)

        # return "\n".join([s.resourceType for s in
        # self.supported_resource.all()])
        return rOpenType

    def get_open_resource_count(self):
        rOpenTypeCount = 0
        for s in self.supported_resource.all():
            if not s.secure_access:
                rOpenTypeCount += 1

        return rOpenTypeCount

    def get_protected_resource_count(self):
        rProtectedTypeCount = 0
        for s in self.supported_resource.all():
            if s.secure_access:
                rProtectedTypeCount += 1

        return rProtectedTypeCount

    def server_address_text(self):
        server_address_text = self.server_address
        return server_address_text

    def fhir_url_text(self):
        fhir_url_text = self.fhir_url

        return fhir_url_text


class SupportedResourceType(models.Model):
    # unique resource_name
    resource_name = models.CharField(max_length=255,
                                     unique=True,
                                     db_index=True,
                                     verbose_name="unique Resource "
                                                  "name in this table")
    # FHIR_Server
    fhir_source = models.ForeignKey(ResourceRouter,
                                    on_delete=CASCADE,
                                    blank=True,
                                    null=True)
    # fhir_resourceType
    resourceType = models.CharField(max_length=250,
                                    unique=False,
                                    db_index=True,
                                    verbose_name="Actual FHIR Resource Type")
    # should user be logged in to access this resource
    secure_access = models.BooleanField(default=True,
                                        verbose_name="Secured resource",
                                        help_text='Login required to access'
                                                  ' this resource')
    json_schema = models.TextField(max_length=5120,
                                   default='{}',
                                   help_text='{} indicates no schema.')
    get = models.BooleanField(default=False,
                              verbose_name='get',
                              help_text='FHIR Interaction Type')
    read = models.BooleanField(default=False,
                               verbose_name='read',
                               help_text='FHIR Interaction Type')
    vread = models.BooleanField(default=False,
                                verbose_name='vread',
                                help_text='FHIR Interaction Type')
    history = models.BooleanField(default=False,
                                  verbose_name='_history',
                                  help_text='FHIR Interaction Type')
    search = models.BooleanField(default=False,
                                 verbose_name='search',
                                 help_text='FHIR Interaction Type')
    put = models.BooleanField(default=False,
                              verbose_name='put',
                              help_text='FHIR Interaction Type')
    create = models.BooleanField(default=False,
                                 verbose_name='create',
                                 help_text='FHIR Interaction Type')
    update = models.BooleanField(default=False,
                                 verbose_name='update',
                                 help_text='FHIR Interaction Type')
    patch = models.BooleanField(default=False,
                                verbose_name='patch',
                                help_text='FHIR Interaction Type')
    delete = models.BooleanField(default=False,
                                 verbose_name='delete',
                                 help_text='FHIR Interaction Type')
    # override_url_id indicates that we change the ID part of the URL
    # in order to prevent a user requesting another person's information
    # This is typically used on the Patient Resource for BlueButton
    # The Bluebutton.Crosswalk is used to get the user's URL Id for the
    # patient Resource
    override_url_id = models.BooleanField(default=False,
                                          help_text="Does this resource need "
                                                    "to mask the id in the "
                                                    "url?")
    # override_search is used to determine if the ?{Search parameters need
    # to be evaluated to Add or Remove  elements of the search string
    # This is used in BlueButton to apply a Patient=Patient_ID to requests
    # for ExplanationOfBenefit so that only the EOBs for the specific user
    # are returned.
    override_search = models.BooleanField(default=False,
                                          help_text="Do search parameters "
                                                    "need to be filtered "
                                                    "to avoid revealing "
                                                    "other people's data?")
    # search_block is a list stored as text
    # search_block will remove parameters from the search string
    search_block = models.TextField(max_length=5120,
                                    blank=True,
                                    default="",
                                    help_text="list of values that need to be "
                                              "removed from search "
                                              "parameters. eg. <b>Patient</b>")
    # search_add is a list stored as text
    # search_add will add a filter parameter to the search string
    # In BlueButton this is used to add the patient_url_id to the search string
    # We currently use %PATIENT% to do a replace with patient_id
    search_add = models.TextField(max_length=200,
                                  blank=True,
                                  default="",
                                  help_text="list of keys that need to be "
                                            "added to search parameters to "
                                            "filter information that is "
                                            "returned. eg. "
                                            "<b>Patient=%PATIENT%</b>")

    def __str__(self):
        return self.resource_name

    def get_supported_interaction_types(self):
        sit = []
        if self.get:
            sit.append(str(self._meta.get_field('get').verbose_name).lower())
        if self.put:
            sit.append(str(self._meta.get_field('put').verbose_name).lower())
        if self.create:
            sit.append(str(self._meta.get_field('create').verbose_name).lower())
        if self.read:
            sit.append(str(self._meta.get_field('read').verbose_name).lower())
        if self.vread:
            sit.append(str(self._meta.get_field('vread').verbose_name).lower())
        if self.update:
            sit.append(str(self._meta.get_field('update').verbose_name).lower())
        if self.patch:
            sit.append(str(self._meta.get_field('patch').verbose_name).lower())
        if self.delete:
            sit.append(str(self._meta.get_field('delete').verbose_name).lower())
        if self.search:
            sit.append(str(self._meta.get_field('search').verbose_name).lower())
        if self.history:
            sit.append(str(self._meta.get_field('history').verbose_name).lower())
        return sit

    def set_search_block(self, x):
        # Convert list to text

        # Done: get text, convert to list, add x, save back as text
        self.search_block = init_text_list(x)

    def get_search_block(self):
        # get search_block and convert to list from text
        # Done: fix conversion from text to list
        # if self.search_block == '':
        #     search_list = '[]'
        # else:
        #     search_list = self.search_block
        # return json.loads(search_list)

        return text_to_list(self.search_block)

    def set_search_add(self, x):
        # Add x to search_add.
        # Done: get text, convert to list, add x, save back as text
        self.search_add = init_text_list(x)

    def get_search_add(self):
        # Done: get text, convert to list
        # if self.search_add == '':
        #     search_list = '[]'
        # else:
        #     search_list = [self.search_add, ]

        return text_to_list(self.search_add)

    def access_denied(self, access_to_check):
        # TODO: write the proper logic
        # return True
        if access_to_check.lower() == 'fhir_get':
            return not self.get
        elif access_to_check.lower() == 'fhir_put':
            return not self.put
        elif access_to_check.lower() == 'fhir_create':
            return not self.create
        elif access_to_check.lower() == 'fhir_read':
            return not self.read
        elif access_to_check.lower() == 'fhir_update':
            return not self.update
        elif access_to_check.lower() == 'fhir_patch':
            return not self.patch
        elif access_to_check.lower() == 'fhir_delete':
            return not self.delete
        elif access_to_check.lower() == 'fhir_search':
            return not self.search
        elif access_to_check.lower() == 'fhir_history':
            return not self.history
        else:
            return True

    def access_permitted(self, access_to_check):
        # TODO: write the proper logic
        # return True
        if access_to_check.lower() == 'fhir_get':
            return self.get
        elif access_to_check.lower() == 'fhir_put':
            return self.put
        elif access_to_check.lower() == 'fhir_create':
            return self.create
        elif access_to_check.lower() == 'fhir_read':
            return self.read
        elif access_to_check.lower() == 'fhir_update':
            return self.update
        elif access_to_check.lower() == 'fhir_patch':
            return self.patch
        elif access_to_check.lower() == 'fhir_delete':
            return self.delete
        elif access_to_check.lower() == 'fhir_search':
            return self.search
        elif access_to_check.lower() == 'fhir_history':
            return self.history
        else:
            return False

    def login_to_access(self):
        # Should the user be logged in to access this resource
        return self.secure_access
