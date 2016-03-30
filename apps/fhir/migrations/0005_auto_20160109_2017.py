# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0004_auto_20160109_2017'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_create',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_delete',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_get',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_history',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_put',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_read',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_search',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_update',
        ),
        migrations.RemoveField(
            model_name='supportedresourcetype',
            name='fhir_vread',
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='create',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'create'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='delete',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'delete'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='get',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'get'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='history',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'_history'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='put',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'put'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='read',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'read'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='search',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'search'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='update',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'update'),
        ),
        migrations.AddField(
            model_name='supportedresourcetype',
            name='vread',
            field=models.BooleanField(default=False, help_text=b'FHIR Interaction Type', verbose_name=b'vread'),
        ),
    ]
