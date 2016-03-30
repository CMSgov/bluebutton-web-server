# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_create',
            field=models.BooleanField(default=False, verbose_name=b'Create'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_delete',
            field=models.BooleanField(default=False, verbose_name=b'DELETE'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_get',
            field=models.BooleanField(default=True, verbose_name=b'GET'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_history',
            field=models.BooleanField(default=False, verbose_name=b'_history'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_put',
            field=models.BooleanField(default=False, verbose_name=b'PUT'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_read',
            field=models.BooleanField(default=True, verbose_name=b'Read'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_search',
            field=models.BooleanField(default=True, verbose_name=b'Search'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_update',
            field=models.BooleanField(default=False, verbose_name=b'Update'),
        ),
    ]
