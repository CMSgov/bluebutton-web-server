# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capabilities', '0002_auto_20160215_1439'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='protectedcapability',
            options={'verbose_name': 'Protected Capability', 'verbose_name_plural': 'Protected Capabilities'},
        ),
        migrations.AlterField(
            model_name='protectedcapability',
            name='title',
            field=models.CharField(default=b'', unique=True, max_length=256),
        ),
    ]
