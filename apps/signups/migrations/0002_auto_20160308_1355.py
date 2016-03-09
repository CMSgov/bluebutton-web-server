# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertifyingBody',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iss', models.CharField(default=b'', help_text=b'Must contain a QDN', max_length=512, verbose_name=b'Issuer')),
                ('verified', models.BooleanField(default=False)),
                ('email', models.EmailField(default=b'', max_length=256)),
                ('title', models.CharField(default=b'', max_length=256, blank=True)),
                ('website_url', models.CharField(default=b'', max_length=512, blank=True)),
                ('public_cert_url', models.CharField(default=b'', help_text=b'A link to the public cert corresponding to the private certificate used to sign software statements.', max_length=512, verbose_name=b'Public Certificate URL', blank=True)),
                ('first_name', models.CharField(default=b'', max_length=512, blank=True)),
                ('last_name', models.CharField(default=b'', max_length=512, blank=True)),
                ('organization_name', models.CharField(default=b'', max_length=512, blank=True)),
                ('notes', models.TextField(default=b'', max_length=512, blank=True)),
                ('created', models.DateField(auto_now_add=True)),
                ('updated', models.DateField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Certifying Body',
            },
        ),
        migrations.DeleteModel(
            name='Endorser',
        ),
    ]
