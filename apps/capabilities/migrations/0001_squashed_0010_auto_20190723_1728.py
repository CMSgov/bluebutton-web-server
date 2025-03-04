# Generated by Django 2.2.22 on 2021-05-13 18:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('capabilities', '0001_initial'), ('capabilities', '0002_auto_20160613_1243'), ('capabilities', '0003_auto_20160621_0803'), ('capabilities', '0004_auto_20160720_1816'), ('capabilities', '0004_auto_20160708_0420'), ('capabilities', '0005_merge'), ('capabilities', '0006_auto_20170423_2201'), ('capabilities', '0007_merge'), ('capabilities', '0006_auto_20170517_1350'), ('capabilities', '0008_merge'), ('capabilities', '0009_protectedcapability_default'), ('capabilities', '0010_auto_20190723_1728')]

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectedCapability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='', max_length=255, unique=True)),
                ('slug', models.CharField(default='', max_length=255, unique=True, verbose_name='Scope')),
                ('protected_resources', models.TextField(default='[["GET", "/some-url"]]', help_text='A JSON list of pairs containing HTTP method and URL.\n        It may contain [id] placeholders for wildcards\n        Example: [["GET","/api/task1"], ["POST","/api/task2/[id]"]]')),
                ('description', models.TextField(blank=True, default='', max_length=10240)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group')),
                ('default', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Protected Capabilities',
                'verbose_name': 'Protected Capability',
            },
        ),
    ]
