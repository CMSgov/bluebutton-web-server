# apps/dot_ext/migrations/0013_add_include_samhsa_to_accesstoken.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dot_ext', '0012_bluebutton_access_token'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                ALTER TABLE oauth2_provider_accesstoken 
                ADD COLUMN IF NOT EXISTS include_samhsa boolean NOT NULL DEFAULT false;
            ''',
            reverse_sql='ALTER TABLE oauth2_provider_accesstoken DROP COLUMN IF EXISTS include_samhsa;',
        ),
    ]