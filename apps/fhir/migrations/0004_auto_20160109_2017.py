# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0003_auto_20160109_1919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportedresourcetype',
            name='fhir_history',
            field=models.BooleanField(default=False, verbose_name=b'_history'),
        ),
    ]
