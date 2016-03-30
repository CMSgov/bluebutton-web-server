# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_name', models.CharField(unique=True, max_length=256, db_index=True)),
                ('json_schema', models.TextField(default=b'{}', help_text=b'{} indicates no schema.', max_length=5120)),
            ],
        ),
    ]
