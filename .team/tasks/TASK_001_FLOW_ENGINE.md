# 任务001：任务流程可视化引擎

## 任务描述
构建完整的任务流程可视化系统，支持任务发起、节点流转、转交记录、超时预警。

## 详细需求

### 1. 任务发起记录
- 发起人（User外键）
- 起始时间（created_at）
- 关联项目（Project外键）
- 任务标题和描述

### 2. 节点活动记录 (StageActivity)
每条记录包含：
- 节点名称
- 进入时间
- 离开时间
- 处理人（谁处理的）
- 处理动作（批准/拒绝/转交/完成）
- 处理备注
- 转交目标（如果是转交）

### 3. 转交记录
- 原负责人 → 新负责人
- 转交原因
- 转交时间
- 是否被拒绝

### 4. 超时预警
- 每个节点可设置超时时间
- 接近超时时预警（ Celery定时任务）
- 超时后状态变更

### 5. 当前环节
- 实时查询任务当前停留在哪个节点
- 动态计算整体进度

## 现有模型（参考）

```
# tasks/models.py 现有模型
class Task(models.Model):
    title, description, project, creator, assignee, status, priority, ...

# approvals/models.py 现有模型  
class ApprovalFlow, ApprovalNode, ...
```

## 实现步骤

### 步骤1：分析现有模型
- 读取 `tasks/models.py`
- 读取 `approvals/models.py`
- 分析如何整合

### 步骤2：设计StageActivity模型
```python
class StageActivity(models.Model):
    task = ForeignKey(Task)
    stage_name = CharField
    enter_time = DateTimeField
    exit_time = DateTimeField (nullable)
    handler = ForeignKey(User, null=True)
    action = CharField (approve/reject/transfer/complete)
    remarks = TextField (nullable)
    transfer_to = ForeignKey(User, null=True)
    is_timeout = BooleanField(default=False)
```

### 步骤3：实现流程引擎
- 创建 `apps/flow_engine/` app
- 实现 FlowEngine 类
- 支持：发起、流转、转交、完成

### 步骤4：实现超时检测
- Celery task 检测超时节点
- 发送通知

### 步骤5：编写API
- REST API 支持前端查询

## 交付物
- `apps/flow_engine/` 完整模块
- 数据库迁移文件
- 单元测试
- API接口文档

## 验收标准
- [ ] 可以发起新任务并记录发起人/时间
- [ ] 任务流转有完整的StageActivity记录
- [ ] 支持转交且有转交记录
- [ ] 可以查询任务当前节点
- [ ] 有超时预警机制
