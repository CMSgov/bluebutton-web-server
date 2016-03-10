# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0004_auto_20160216_2128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='endorsements',
            field=models.ManyToManyField(to='dot_ext.Endorsement', blank=True),
        ),
    ]
