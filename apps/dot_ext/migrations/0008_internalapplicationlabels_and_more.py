# Generated by Django 4.2.17 on 2025-01-25 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0007_merge_20231020_2004'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalApplicationLabels',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(default='', max_length=255, unique=True)),
                ('slug', models.CharField(default='', max_length=1024, unique=True)),
                ('description', models.TextField(blank=True, default='', max_length=10240)),
            ],
            options={
                'verbose_name': 'Internal Application Label',
                'verbose_name_plural': 'Internal Application Labels',
            },
        ),
        migrations.AlterField(
            model_name='application',
            name='data_access_type',
            field=models.CharField(choices=[('ONE_TIME', 'ONE_TIME - No refresh token needed.'), ('RESEARCH_STUDY', 'RESEARCH_STUDY - No expiration.'), ('THIRTEEN_MONTH', 'THIRTEEN_MONTH - Access expires in 13-months.')], default='THIRTEEN_MONTH', max_length=16, null=True, verbose_name='Data Access Type:'),
        ),
        migrations.AddField(
            model_name='application',
            name='internal_application_labels',
            field=models.ManyToManyField(to='dot_ext.internalapplicationlabels'),
        ),
    ]
