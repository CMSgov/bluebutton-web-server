# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0005_auto_20160308_1355'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpiresIn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=64)),
                ('expires_in', models.IntegerField()),
            ],
        ),
    ]
