# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capabilities', '0003_auto_20160215_2044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='protectedcapability',
            name='slug',
            field=models.SlugField(default=b'', unique=True, max_length=100, verbose_name=b'Scope'),
        ),
    ]
