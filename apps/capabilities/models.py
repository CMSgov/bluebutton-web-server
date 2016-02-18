from __future__ import absolute_import
from __future__ import unicode_literals

import json

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import Group


@python_2_unicode_compatible
class ProtectedCapability(models.Model):
    title               = models.CharField(max_length=256, default="", unique=True)
    slug                = models.SlugField(verbose_name="Scope", max_length=100, default="", unique=True)
    group               = models.ForeignKey(Group)
    protected_resources = models.TextField(max_length=10240,
                            help_text="""A JSON list of pairs containing HTTP method and URL.
                            Example: [["GET","/api/task1"], ["POST","/api/task2"]]
                            """, default="""[["GET", "/some-url"]]""")
    description         = models.TextField(max_length=10240, blank=True, default="")

    def __str__(self):
        return self.title

    def resources_as_dict(self):
        """
        Return protected_resources mapped into a dictionary.
        e.g. {"GET": ["/api/example1", "/api/example2"], "POST": ... }
        """
        protected_resources = {}
        for method, path in json.loads(self.protected_resources):
            if method not in protected_resources:
                protected_resources[method] = [path]
            else:
                protected_resources[method].append(path)
        return protected_resources

    def scope(self):
        return self.slug

    class Meta:
        verbose_name_plural = "Protected Capabilities"
        verbose_name        = "Protected Capability"
