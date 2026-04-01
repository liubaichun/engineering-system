# Data migration: convert CharField client/supplier to empty strings
# that will be replaced by proper FK columns in 0004.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0002_initial'),
    ]

    operations = [
        # Set non-numeric text values to empty string to satisfy NOT NULL
        # These rows will get NULL FK after the column type change in 0004
        migrations.RunSQL(
            sql="""
                UPDATE projects SET client = '' WHERE client IS NOT NULL AND client != '' AND client !~ '^[0-9]+$';
                UPDATE projects SET supplier = '' WHERE supplier IS NOT NULL AND supplier != '' AND supplier !~ '^[0-9]+$';
            """,
            reverse_sql="",
        ),
    ]
