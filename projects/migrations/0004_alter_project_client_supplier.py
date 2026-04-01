# Converts client/supplier from CharField to FK using proper column replacement
# that handles the NOT NULL → NULL FK transition safely.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0003_nullify_text_client_supplier'),
        ('crm', '0002_customer_supplier_alter_client_options'),
    ]

    operations = [
        # Step 1: Add new nullable FK columns
        migrations.AddField(
            model_name='project',
            name='client_new',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='crm.customer',
                verbose_name='客户'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='supplier_new',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='crm.supplier',
                verbose_name='供应商'
            ),
            preserve_default=False,
        ),
        # Step 2: Copy data (numeric strings → FK IDs, rest → NULL)
        migrations.RunSQL(
            sql="""
                UPDATE projects
                SET client_new_id = CASE
                    WHEN client ~ '^[0-9]+$' THEN client::bigint
                    ELSE NULL
                END,
                supplier_new_id = CASE
                    WHEN supplier ~ '^[0-9]+$' THEN supplier::bigint
                    ELSE NULL
                END;
            """,
            reverse_sql="",
        ),
        # Step 3: Remove old CharField columns
        migrations.RemoveField(model_name='project', name='client'),
        migrations.RemoveField(model_name='project', name='supplier'),
        # Step 4: Rename new FK columns to original names
        migrations.RenameField(model_name='project', old_name='client_new', new_name='client'),
        migrations.RenameField(model_name='project', old_name='supplier_new', new_name='supplier'),
    ]
