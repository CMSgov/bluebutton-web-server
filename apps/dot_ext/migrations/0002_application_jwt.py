# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='jwt',
            field=models.TextField(default=b'', max_length=10240, blank=True),
        ),
    ]
