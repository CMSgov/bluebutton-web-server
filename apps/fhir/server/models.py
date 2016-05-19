import json

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class SupportedResourceType(models.Model):
    resource_name           = models.CharField(max_length=256, unique=True,
                                    db_index=True)
    json_schema             = models.TextField(max_length=5120, default="{}",
                                                help_text="{} indicates no schema.")
    get                = models.BooleanField(default=False, verbose_name="get",
                                                    help_text="FHIR Interaction Type")
    put                = models.BooleanField(default=False, verbose_name="put",
                                                  help_text="FHIR Interaction Type")
    create             = models.BooleanField(default=False, verbose_name="create",
                                                  help_text="FHIR Interaction Type")
    read               = models.BooleanField(default=False, verbose_name="read",
                                                  help_text="FHIR Interaction Type")
    vread              = models.BooleanField(default=False, verbose_name="vread",
                                                  help_text="FHIR Interaction Type")
    update             = models.BooleanField(default=False, verbose_name="update",
                                                  help_text="FHIR Interaction Type")
    delete             = models.BooleanField(default=False, verbose_name="delete",
                                                  help_text="FHIR Interaction Type")
    search             = models.BooleanField(default=False, verbose_name="search",
                                                  help_text="FHIR Interaction Type")
    history            = models.BooleanField(default=False, verbose_name="_history",
                                                  help_text="FHIR Interaction Type")

    # Python2 uses __unicode__(self):

    def __str__(self):
        return self.resource_name

    def get_supported_interaction_types(self):
        sit = []
        if self.get:
            sit.append(self._meta.get_field("get").verbose_name)
        if self.put:
            sit.append(self._meta.get_field("put").verbose_name)
        if self.create:
            sit.append(self._meta.get_field("create").verbose_name)
        if self.read:
            sit.append(self._meta.get_field("read").verbose_name)
        if self.vread:
            sit.append(self._meta.get_field("vread").verbose_name)
        if self.update:
            sit.append(self._meta.get_field("update").verbose_name)
        if self.delete:
            sit.append(self._meta.get_field("delete").verbose_name)
        if self.search:
            sit.append(self._meta.get_field("search").verbose_name)
        if self.history:
            sit.append(self._meta.get_field("history").verbose_name)
        return sit


    def access_denied(self, access_to_check):
        return True
        # if access_to_check.lower() == "fhir_get":
        #     return not self.fhir_get
        # elif access_to_check.lower() == "fhir_put":
        #     return not self.fhir_put
        # elif access_to_check.lower() == "fhir_create":
        #     return not self.fhir_create
        # elif access_to_check.lower() == "fhir_read":
        #     return not self.fhir_read
        # elif access_to_check.lower() == "fhir_update":
        #     return not self.fhir_update
        # elif access_to_check.lower() == "fhir_delete":
        #     return not self.fhir_delete
        # elif access_to_check.lower() == "fhir_search":
        #     return not self.fhir_search
        # elif access_to_check.lower() == "fhir_history":
        #     return not self.fhir_history
        # else:
        #     return True

    def access_permitted(self, access_to_check):
        return True
        # if access_to_check.lower() == "fhir_get":
        #     return self.fhir_get
        # elif access_to_check.lower() == "fhir_put":
        #     return self.fhir_put
        # elif access_to_check.lower() == "fhir_create":
        #     return self.fhir_create
        # elif access_to_check.lower() == "fhir_read":
        #     return self.fhir_read
        # elif access_to_check.lower() == "fhir_update":
        #     return self.fhir_update
        # elif access_to_check.lower() == "fhir_delete":
        #     return self.fhir_delete
        # elif access_to_check.lower() == "fhir_search":
        #     return self.fhir_search
        # elif access_to_check.lower() == "fhir_history":
        #     return self.fhir_history
        # else:
        #     return False


@python_2_unicode_compatible
class ResourceTypeControl(models.Model):
    resource_name      = models.ForeignKey(SupportedResourceType)
    override_url_id    = models.BooleanField(help_text="Does this resource need to mask "
                                                       "the id in the url?")
    override_search    = models.BooleanField(help_text="Do search parameters need to be "
                                                       "filtered to avoid revealing "
                                                       "other people's data?")
    search_block       = models.TextField(max_length=5120, default="",
                                          help_text="list of values that need to be removed "
                                                    "from search parameters. eg. Patient")
    search_add         = models.TextField(max_length=200, default="",
                                          help_text="list of keys that need to be added to"
                                                    "search parameters to filter information"
                                                    "that is returned. eg. Patient.")
    group_allow        = models.TextField(max_length=100, default="",
                                          help_text="groups permitted to access resource.")
    group_exclude      = models.TextField(max_length=100, default="",
                                          help_text="groups blocked from accessing resource.")

    # Python2 uses __unicode__(self):
    def __str__(self):
        return self.resource_name.resource_name

    def set_search_block(self, x):
        self.search_block = json.dumps(x)

    def get_search_block(self, x):
        return json.loads(self.search_block)

    def set_search_add(self, x):
        self.search_add = json.dumps(x)

    def get_search_add(self, x):
        return json.loads(self.search_add)

    def replace_url_id(self):
        return self.override_url_id

    def set_group_allow(self, x):
        self.group_allow = json.dumps(x)

    def get_group_allow(self, x):
        return json.loads(self.group_allow)

    def set_group_exclude(self, x):
        self.group_exclude = json.dumps(x)

    def get_group_exclude(self, x):
        return json.loads(self.group_exclude)

