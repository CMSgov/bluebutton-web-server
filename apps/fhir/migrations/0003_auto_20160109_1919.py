# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0002_auto_20160109_1902'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportedresourcetype',
            name='fhir_vread',
            field=models.BooleanField(default=False, verbose_name=b'vread'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_create',
            field=models.BooleanField(default=False, verbose_name=b'create'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_delete',
            field=models.BooleanField(default=False, verbose_name=b'delete'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_get',
            field=models.BooleanField(default=False, verbose_name=b'get'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_history',
            field=models.BooleanField(default=False, verbose_name=b'history'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_put',
            field=models.BooleanField(default=False, verbose_name=b'put'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_read',
            field=models.BooleanField(default=False, verbose_name=b'read'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_search',
            field=models.BooleanField(default=False, verbose_name=b'search'),
        ),
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_update',
            field=models.BooleanField(default=False, verbose_name=b'update'),
        ),
    ]
