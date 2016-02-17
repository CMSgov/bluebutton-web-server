# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0003_auto_20160216_2106'),
    ]

    operations = [
        migrations.CreateModel(
            name='Endorsement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField(default=b'', max_length=256)),
                ('iss', models.TextField(default=b'', help_text=b'Must contain a QDN', max_length=512, verbose_name=b'Issuer')),
                ('jws', models.TextField(default=b'', max_length=10240)),
            ],
        ),
        migrations.RenameField(
            model_name='application',
            old_name='protected_capability',
            new_name='scope',
        ),
        migrations.RemoveField(
            model_name='application',
            name='jwt',
        ),
        migrations.AddField(
            model_name='application',
            name='endorsements',
            field=models.ManyToManyField(to='dot_ext.Endorsement'),
        ),
    ]
