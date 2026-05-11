from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0011_remove_application_allow_client_credentials_and_more'),
        ('oauth2_provider', '0006_alter_application_client_secret'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='BlueButtonAccessToken',
                    fields=[
                        ('id', models.BigAutoField(
                            auto_created=True,
                            primary_key=True,
                            serialize=False,
                            verbose_name='ID'
                        )),
                        ('include_samhsa', models.BooleanField(default=False)),
                    ],
                    options={
                        'db_table': 'oauth2_provider_accesstoken',
                        'swappable': 'OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]