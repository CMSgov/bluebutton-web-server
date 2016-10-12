import json
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SupportedResourceType(models.Model):
    resource_name = models.CharField(max_length=255,
                                     unique=True,
                                     db_index=True)
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
    # search_block will remove parameters from the search string
    search_block = models.TextField(max_length=5120,
                                    blank=True,
                                    default="",
                                    help_text="list of values that need to be "
                                              "removed from search "
                                              "parameters. eg. <b>Patient</b>")
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
            sit.append(self._meta.get_field('get').verbose_name)
        if self.put:
            sit.append(self._meta.get_field('put').verbose_name)
        if self.create:
            sit.append(self._meta.get_field('create').verbose_name)
        if self.read:
            sit.append(self._meta.get_field('read').verbose_name)
        if self.vread:
            sit.append(self._meta.get_field('vread').verbose_name)
        if self.update:
            sit.append(self._meta.get_field('update').verbose_name)
        if self.patch:
            sit.append(self._meta.get_field('patch').verbose_name)
        if self.delete:
            sit.append(self._meta.get_field('delete').verbose_name)
        if self.search:
            sit.append(self._meta.get_field('search').verbose_name)
        if self.history:
            sit.append(self._meta.get_field('history').verbose_name)
        return sit

    def set_search_block(self, x):
        self.search_block = json.dumps(x)

    def get_search_block(self):
        if self.search_block == '':
            search_list = []
        else:
            search_list = self.search_block
        return json.loads(search_list)

    def set_search_add(self, x):
        self.search_add = json.dumps(x)

    def get_search_add(self):
        if self.search_add == '':
            search_list = []
        else:
            search_list = [self.search_add, ]
        return search_list

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


@python_2_unicode_compatible
class ResourceRouter(models.Model):
    """
    If SupportedResourceType is not hosted on default server
    then enter the server url here.
    Enter full URL and path
    """
    supported_resource = models.ForeignKey(SupportedResourceType)
    fhir_path = models.URLField(blank=True,
                                verbose_name="Default FHIR URL with "
                                             "terminating /",
                                help_text="Exclude the resource. eg. "
                                          "<b>https://fhirserver.com/fhir/"
                                          "Patient/</b> is entered as "
                                          "<b>https://fhirserver.com/fhir/"
                                          "</b></br>Leave blank to accept "
                                          "system default.")
    # Add fhir_path unless the resource is defined via crosswalk

    def __str__(self):
        return self.supported_resource.resource_name
