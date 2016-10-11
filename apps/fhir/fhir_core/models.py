#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: models
Created: 10/10/16 10:11 PM

File created by: ''
"""
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
    put = models.BooleanField(default=False,
                              verbose_name='put',
                              help_text='FHIR Interaction Type')
    create = models.BooleanField(default=False,
                                 verbose_name='create',
                                 help_text='FHIR Interaction Type')
    read = models.BooleanField(default=False,
                               verbose_name='read',
                               help_text='FHIR Interaction Type')
    vread = models.BooleanField(default=False,
                                verbose_name='vread',
                                help_text='FHIR Interaction Type')
    update = models.BooleanField(default=False,
                                 verbose_name='update',
                                 help_text='FHIR Interaction Type')
    delete = models.BooleanField(default=False,
                                 verbose_name='delete',
                                 help_text='FHIR Interaction Type')
    search = models.BooleanField(default=False,
                                 verbose_name='search',
                                 help_text='FHIR Interaction Type')
    history = models.BooleanField(default=False,
                                  verbose_name='_history',
                                  help_text='FHIR Interaction Type')

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
        if self.delete:
            sit.append(self._meta.get_field('delete').verbose_name)
        if self.search:
            sit.append(self._meta.get_field('search').verbose_name)
        if self.history:
            sit.append(self._meta.get_field('history').verbose_name)
        return sit

    def access_denied(self, access_to_check):
        # TODO: write the proper logic
        return True
        # if access_to_check.lower() == 'fhir_get':
        #     return not self.fhir_get
        # elif access_to_check.lower() == 'fhir_put':
        #     return not self.fhir_put
        # elif access_to_check.lower() == 'fhir_create':
        #     return not self.fhir_create
        # elif access_to_check.lower() == 'fhir_read':
        #     return not self.fhir_read
        # elif access_to_check.lower() == 'fhir_update':
        #     return not self.fhir_update
        # elif access_to_check.lower() == 'fhir_delete':
        #     return not self.fhir_delete
        # elif access_to_check.lower() == 'fhir_search':
        #     return not self.fhir_search
        # elif access_to_check.lower() == 'fhir_history':
        #     return not self.fhir_history
        # else:
        #     return True

    def access_permitted(self, access_to_check):
        # TODO: write the proper logic
        return True
        # if access_to_check.lower() == 'fhir_get':
        #     return self.fhir_get
        # elif access_to_check.lower() == 'fhir_put':
        #     return self.fhir_put
        # elif access_to_check.lower() == 'fhir_create':
        #     return self.fhir_create
        # elif access_to_check.lower() == 'fhir_read':
        #     return self.fhir_read
        # elif access_to_check.lower() == 'fhir_update':
        #     return self.fhir_update
        # elif access_to_check.lower() == 'fhir_delete':
        #     return self.fhir_delete
        # elif access_to_check.lower() == 'fhir_search':
        #     return self.fhir_search
        # elif access_to_check.lower() == 'fhir_history':
        #     return self.fhir_history
        # else:
        #     return False
