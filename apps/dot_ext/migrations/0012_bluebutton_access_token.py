from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0011_remove_application_allow_client_credentials_and_more'),
        ('oauth2_provider', '0006_alter_application_client_secret'),
    ]

    # operations = [
    #     migrations.RunSQL(
    #         sql='''
    #             ALTER TABLE oauth2_provider_accesstoken 
    #             ADD COLUMN IF NOT EXISTS include_samhsa boolean NOT NULL DEFAULT false;
    #         ''',
    #         reverse_sql='ALTER TABLE oauth2_provider_accesstoken DROP COLUMN IF EXISTS include_samhsa;',
    #     ),
    # ]
    # operations = [
    #     # Update Django's migration state to know about BlueButtonAccessToken
    #     # without actually creating a table (it already exists as oauth2_provider_accesstoken)
    #     migrations.SeparateDatabaseAndState(
    #         state_operations=[
    #             migrations.CreateModel(
    #                 name='BlueButtonAccessToken',
    #                 fields=[
    #                     # Django needs these declared for state tracking
    #                     # Copy from AbstractAccessToken + your new field
    #                     ('include_samhsa', models.BooleanField(default=False)),
    #                 ],
    #                 options={
    #                     'db_table': 'oauth2_provider_accesstoken',
    #                     'swappable': 'OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL',
    #                 },
    #             ),
    #         ],
    #         database_operations=[
    #             # Only run the real ALTER TABLE — no CREATE TABLE
    #             migrations.RunSQL(
    #                 sql='''
    #                     ALTER TABLE oauth2_provider_accesstoken 
    #                     ADD COLUMN IF NOT EXISTS include_samhsa boolean NOT NULL DEFAULT false;
    #                 ''',
    #                 reverse_sql='ALTER TABLE oauth2_provider_accesstoken DROP COLUMN IF EXISTS include_samhsa;',
    #             ),
    #         ],
    #     ),
    # ]
    # operations = [
    #     migrations.SeparateDatabaseAndState(
    #         state_operations=[
    #             migrations.CreateModel(
    #                 name='BlueButtonAccessToken',
    #                 fields=[
    #                     # Must include the primary key so FK references resolve
    #                     ('id', models.BigAutoField(
    #                         auto_created=True,
    #                         primary_key=True,
    #                         serialize=False,
    #                         verbose_name='ID'
    #                     )),
    #                     ('include_samhsa', models.BooleanField(default=False)),
    #                 ],
    #                 options={
    #                     'db_table': 'oauth2_provider_accesstoken',
    #                     'swappable': 'OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL',
    #                 },
    #             ),
    #         ],
    #         database_operations=[
    #             migrations.RunSQL(
    #                 sql='''
    #                     ALTER TABLE oauth2_provider_accesstoken 
    #                     ADD COLUMN IF NOT EXISTS include_samhsa boolean NOT NULL DEFAULT false;
    #                 ''',
    #                 reverse_sql='ALTER TABLE oauth2_provider_accesstoken DROP COLUMN IF EXISTS include_samhsa;',
    #             ),
    #         ],
    #     ),
    # ]
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
            database_operations=[],  # No DB changes — table already exists
        ),
    ]