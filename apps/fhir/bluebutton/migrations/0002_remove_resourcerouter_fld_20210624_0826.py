from django.db import connection
from django.db import migrations

POSTGRES_DROP_COL = "ALTER TABLE {} DROP COLUMN IF EXISTS {};"
SQLITE3_DROP_COL = '''
CREATE TABLE "new__bluebutton_crosswalk" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "fhir_id" varchar(80) NOT NULL UNIQUE, "date_created" datetime NOT NULL, "user_id_type" varchar(1) NOT NULL, "user_id_hash" varchar(64) NOT NULL UNIQUE, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "user_mbi_hash" varchar(64) NULL UNIQUE);
INSERT INTO "new__bluebutton_crosswalk" ("id", "user_id", "fhir_id", "date_created", "user_id_type", "user_id_hash", "user_mbi_hash") SELECT "id", "user_id", "fhir_id", "date_created", "user_id_type", "user_id_hash", "user_mbi_hash" FROM "bluebutton_crosswalk";
DROP TABLE "bluebutton_crosswalk";
ALTER TABLE "new__bluebutton_crosswalk" RENAME TO "bluebutton_crosswalk";
'''

def _get_drop_col_ddl(table_name, col_name):
    ddl_drop_col = 'postgresql'
    if connection.vendor is not None:
        if connection.vendor == 'sqlite':
            ddl_drop_col = SQLITE3_DROP_COL
        elif connection.vendor == 'postgresql':
            ddl_drop_col = POSTGRES_DROP_COL.format(table_name, col_name)
        else:
            raise ValueError("Supported database: postgresql or sqlite3(for test), but connection.vendor={}".format(connection.vendor))
    return ddl_drop_col


class Migration(migrations.Migration):

    dependencies = [
        ('bluebutton', '0001_squashed_0006_auto_20210513_1812'),
    ]

    operations = [
        migrations.RunSQL(_get_drop_col_ddl("bluebutton_crosswalk", "fhir_source_id")),
    ]
