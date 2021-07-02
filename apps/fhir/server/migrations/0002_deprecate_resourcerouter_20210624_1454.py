from django.db import migrations

SQL_DROP_TABLE = "DROP TABLE IF EXISTS {};"


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_squashed_0018_auto_20210513_1812'),
        ('bluebutton', '0002_remove_resourcerouter_fld_20210624_0826'),
    ]

    operations = [
        migrations.RunSQL(SQL_DROP_TABLE.format('server_resourcerouter_supported_resource')),
        migrations.RunSQL(SQL_DROP_TABLE.format('server_supportedresourcetype')),
        migrations.RunSQL(SQL_DROP_TABLE.format('server_resourcerouter')),
    ]
