"""
任务流程模型
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_add_priority_field'),
    ]

    operations = [
        # 创建TaskType表
        migrations.CreateModel(
            name='TaskType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='类型名称')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '任务类型',
                'verbose_name_plural': '任务类型',
                'db_table': 'tasks_tasktype',
            },
        ),
        
        # 创建FlowTemplate表
        migrations.CreateModel(
            name='FlowTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='模板名称')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '流程模板',
                'verbose_name_plural': '流程模板',
                'db_table': 'tasks_flowtemplate',
            },
        ),
        
        # 创建FlowNodeTemplate表
        migrations.CreateModel(
            name='FlowNodeTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='节点名称')),
                ('order', models.IntegerField(default=0, verbose_name='顺序')),
                ('duration_hours', models.IntegerField(default=24, verbose_name='规定处理时长(小时)')),
                ('responsible_type', models.CharField(choices=[('any', '任意人员'), ('user', '指定人员'), ('role', '角色关联')], default='any', max_length=20, verbose_name='负责人类型')),
                ('responsible_users', models.JSONField(blank=True, default=list, verbose_name='指定人员列表')),
                ('responsible_roles', models.JSONField(blank=True, default=list, verbose_name='指定角色列表')),
                ('allowed_actions', models.JSONField(blank=True, default=list, verbose_name='允许的操作')),
                ('notify_on_assign', models.BooleanField(default=True, verbose_name='分配时通知')),
                ('notify_on_overdue', models.BooleanField(default=True, verbose_name='超时提醒')),
                ('is_start', models.BooleanField(default=False, verbose_name='是否为起点')),
                ('is_end', models.BooleanField(default=False, verbose_name='是否为终点')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nodes', to='tasks.flowtemplate', verbose_name='所属模板')),
            ],
            options={
                'verbose_name': '流程节点模板',
                'verbose_name_plural': '流程节点模板',
                'db_table': 'tasks_flownodetemplate',
            },
        ),
        
        # 创建FlowTransition表
        migrations.CreateModel(
            name='FlowTransition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.JSONField(blank=True, default=dict, verbose_name='流转条件')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_transitions', to='tasks.flownodetemplate', verbose_name='起始节点')),
                ('to_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transitions', to='tasks.flownodetemplate', verbose_name='目标节点')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='tasks.flowtemplate')),
            ],
            options={
                'verbose_name': '流程连线',
                'verbose_name_plural': '流程连线',
                'db_table': 'tasks_flowtransition',
            },
        ),
        
        # 创建TaskStageInstance表
        migrations.CreateModel(
            name='TaskStageInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0, verbose_name='顺序')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('in_progress', '处理中'), ('completed', '已完成'), ('skipped', '已跳过'), ('rejected', '已驳回')], default='pending', max_length=20, verbose_name='状态')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('deadline', models.DateTimeField(blank=True, null=True, verbose_name='截止时间')),
                ('is_overdue', models.BooleanField(default=False, verbose_name='是否超时')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '任务阶段实例',
                'verbose_name_plural': '任务阶段实例',
                'db_table': 'tasks_taskstageinstance',
            },
        ),
        
        # 创建StageActivity表
        migrations.CreateModel(
            name='StageActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('create', '创建'), ('start', '开始处理'), ('complete', '完成'), ('upload', '上传文件'), ('signoff', '签收'), ('approve', '审批通过'), ('reject', '驳回'), ('comment', '评论'), ('transfer', '转交'), ('system', '系统操作')], max_length=20, verbose_name='操作类型')),
                ('content', models.TextField(blank=True, verbose_name='活动内容')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='附件')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '节点活动记录',
                'verbose_name_plural': '节点活动记录',
                'db_table': 'tasks_stageactivity',
            },
        ),
        
        # 添加task_type字段到Task表
        migrations.AddField(
            model_name='task',
            name='task_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='tasks.tasktype', verbose_name='任务类型'),
        ),
        
        # 添加flow_template字段到Task表
        migrations.AddField(
            model_name='task',
            name='flow_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='tasks.flowtemplate', verbose_name='流程模板'),
        ),
        
        # 添加current_stage字段到Task表
        migrations.AddField(
            model_name='task',
            name='current_stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_tasks', to='tasks.flownodetemplate', verbose_name='当前阶段'),
        ),
    ]
