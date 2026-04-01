# 审批流模块部署指南

## 代码部署

将以下文件复制到服务器的 `/var/www/engineering_system/` 目录下：

```
approvals/
├── __init__.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── tasks.py
├── signals.py
├── celery.py
└── DEPLOYMENT.md
```

## 数据库迁移

### 1. 创建审批流表

```bash
cd /var/www/engineering_system
source venv/bin/activate
python manage.py makemigrations approvals
python manage.py migrate
```

### 2. 为 Material 模型添加 low_stock_threshold 字段（如不存在）

```bash
# 如果 Material 模型还没有 low_stock_threshold 字段
python manage.py makemigrations inventory --name add_low_stock_threshold
python manage.py migrate
```

### 3. 为 Equipment 模型确认 maintenance_due 字段存在

根据之前的修复记录，`maintenance_due` 字段已添加到 Equipment 模型。

## 安装依赖

```bash
pip install celery redis
```

## Celery 配置

### 1. 修改 `/var/www/engineering_system/engineering/celery.py`

在 Celery 配置中添加：

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # 每天早上9点检查设备维保到期情况
    'check-equipment-maintenance-daily': {
        'task': 'approvals.tasks.check_equipment_maintenance_due',
        'schedule': crontab(hour=9, minute=0),
    },
    # 每天早上9点检查物料低库存
    'check-material-low-stock-daily': {
        'task': 'approvals.tasks.check_material_low_stock',
        'schedule': crontab(hour=9, minute=0),
    },
    # 每周一早上9点检查项目预算
    'check-project-budget-weekly': {
        'task': 'approvals.tasks.check_project_budget_warning',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}
```

### 2. 启动 Celery Worker

```bash
celery -A engineering_system worker -l INFO -D
```

### 3. 启动 Celery Beat

```bash
celery -A engineering_system beat -l INFO -D
```

## API 测试

### 1. 获取 Token

```bash
# 登录获取token
curl -X POST http://43.156.139.37/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2026"}'
```

### 2. 测试审批流 API

```bash
TOKEN="your-token-here"

# 列出待我审批
curl -X GET http://43.156.139.37/api/v1/approvals/ \
  -H "Authorization: Token $TOKEN"

# 我发起的审批
curl -X GET http://43.156.139.37/api/v1/approvals/my/ \
  -H "Authorization: Token $TOKEN"

# 创建付款审批
curl -X POST http://43.156.139.37/api/v1/approvals/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试付款审批",
    "flow_type": "payment",
    "expense": 1
  }'

# 批准审批
curl -X PATCH http://43.156.139.37/api/v1/approvals/1/approve/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "同意付款"}'

# 拒绝审批
curl -X PATCH http://43.156.139.37/api/v1/approvals/1/reject/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "不同意"}'
```

## 模型说明

### ApprovalFlow（审批流）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str | 审批名称 |
| flow_type | str | 审批类型：payment/project/change |
| status | str | 状态：pending/approved/rejected |
| created_by | FK | 申请人 |
| created_at | datetime | 创建时间 |
| project | FK | 关联项目（立项审批用） |
| expense | FK | 关联支出（付款审批用） |

### ApprovalNode（审批节点）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| flow | FK | 所属审批流 |
| approver | FK | 审批人 |
| node_order | int | 审批顺序 |
| status | str | 状态：pending/approved/rejected |
| comment | text | 审批意见 |
| decided_at | datetime | 审批时间 |
