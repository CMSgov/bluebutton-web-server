# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectedProgram',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', max_length=256)),
                ('slug', models.SlugField(default=b'', unique=True, max_length=100)),
                ('protected_resources', models.TextField(default=b'[["GET", "/some-url"]]', help_text=b'A JSON list of pairs containing HTTP method and URL.\n                            Example: [["GET","/api/task1"], ["POST","/api/task2"]]\n                            ', max_length=10240)),
                ('description', models.TextField(default=b'', max_length=10240, blank=True)),
                ('group', models.ForeignKey(to='auth.Group')),
            ],
        ),
    ]
