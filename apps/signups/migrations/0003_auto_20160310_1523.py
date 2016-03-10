# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signups', '0002_auto_20160308_1355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='certifyingbody',
            options={'verbose_name_plural': 'Certifying Bodies'},
        ),
        migrations.AlterField(
            model_name='certifyingbody',
            name='iss',
            field=models.CharField(default=b'', help_text=b'Must contain a QDN', unique=True, max_length=512, verbose_name=b'Issuer'),
        ),
    ]
