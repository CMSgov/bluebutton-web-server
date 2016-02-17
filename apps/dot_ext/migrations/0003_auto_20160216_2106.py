# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capabilities', '0004_auto_20160216_2106'),
        ('dot_ext', '0002_application_jwt'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='protected_capability',
        ),
        migrations.AddField(
            model_name='application',
            name='protected_capability',
            field=models.ManyToManyField(to='capabilities.ProtectedCapability'),
        ),
    ]
