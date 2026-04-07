# Manual migration to add missing fields to ApprovalFlow
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_approval_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalflow',
            name='applicant_role',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='申请人角色'),
        ),
        migrations.AddField(
            model_name='approvalflow',
            name='current_approver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pending_approvals', to='users.user', verbose_name='当前审批人'),
        ),
        migrations.AddField(
            model_name='approvalflow',
            name='project_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='关联项目ID'),
        ),
    ]
