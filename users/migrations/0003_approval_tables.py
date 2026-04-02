from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_email_unique'),
    ]

    operations = [
        # 1. users_pending_approval（待审核用户申请表）
        migrations.CreateModel(
            name='UsersPendingApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, unique=True, verbose_name='用户名')),
                ('password', models.CharField(max_length=255, verbose_name='密码')),
                ('email', models.EmailField(max_length=254, verbose_name='邮箱')),
                ('role', models.CharField(default='worker', max_length=20, verbose_name='申请角色')),
                ('phone', models.CharField(blank=True, default='', max_length=20, verbose_name='手机号')),
                ('status', models.CharField(default='pending', max_length=20, verbose_name='状态')),
                ('rejection_reason', models.TextField(blank=True, default='', verbose_name='拒绝原因')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='申请时间')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_users', to='users.user', verbose_name='审核人')),
            ],
            options={'verbose_name': '待审核用户', 'verbose_name_plural': '待审核用户', 'db_table': 'users_pending_approval'},
        ),

        # 2. approval_flow（审批流程主表）
        migrations.CreateModel(
            name='ApprovalFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flow_type', models.CharField(max_length=20, verbose_name='流程类型')),
                ('target_object_type', models.CharField(blank=True, default='', max_length=50, verbose_name='目标对象类型')),
                ('target_object_id', models.IntegerField(blank=True, null=True, verbose_name='目标对象ID')),
                ('status', models.CharField(default='pending', max_length=20, verbose_name='状态')),
                ('current_node', models.IntegerField(default=1, verbose_name='当前节点')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_flows', to='users.user', verbose_name='申请人')),
            ],
            options={'verbose_name': '审批流程', 'verbose_name_plural': '审批流程', 'db_table': 'approval_flow'},
        ),

        # 3. approval_record（审批记录明细表）
        migrations.CreateModel(
            name='ApprovalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('node', models.IntegerField(default=1, verbose_name='节点序号')),
                ('action', models.CharField(max_length=20, verbose_name='操作')),
                ('comment', models.TextField(blank=True, default='', verbose_name='审批意见')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='操作时间')),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approval_records', to='users.user', verbose_name='审批人')),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='users.approvalflow', verbose_name='所属流程')),
            ],
            options={'verbose_name': '审批记录', 'verbose_name_plural': '审批记录', 'db_table': 'approval_record'},
        ),

        # 4. user_role_assignment（用户角色分配表）
        migrations.CreateModel(
            name='UserRoleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=20, verbose_name='角色')),
                ('assigned_at', models.DateTimeField(auto_now_add=True, verbose_name='分配时间')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='过期时间')),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='role_assignments_given', to='users.user', verbose_name='分配人')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignments', to='users.user', verbose_name='用户')),
            ],
            options={'verbose_name': '用户角色分配', 'verbose_name_plural': '用户角色分配', 'db_table': 'user_role_assignment'},
        ),

        # 5. role_permission（角色权限表）
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=20, verbose_name='角色')),
                ('resource', models.CharField(max_length=100, verbose_name='资源路径')),
                ('action', models.CharField(max_length=20, verbose_name='操作类型')),
                ('permission_type', models.CharField(default='allow', max_length=20, verbose_name='权限类型')),
            ],
            options={'verbose_name': '角色权限', 'verbose_name_plural': '角色权限', 'db_table': 'role_permission'},
        ),

        # 6. User模型扩展字段（如果还没有的话）
        migrations.AddField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(default=False, verbose_name='是否审批通过'),
        ),
        migrations.AddField(
            model_name='user',
            name='approval_status',
            field=models.CharField(default='pending', max_length=20, verbose_name='审批状态'),
        ),
    ]
