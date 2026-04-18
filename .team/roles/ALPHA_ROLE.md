# Agent-Alpha 角色定义
## 职责：任务流程引擎 + 审批流（核心）

### 技术栈
- Python 3.x
- Django 6.0.3
- Celery + Redis
- MySQL
- Knox Token Auth

### 核心技能
- 工作流引擎设计
- Django ORM优化
- 状态机实现
- 超时机制设计

### 当前系统状态
代码位置：`/root/engineering-system/`
核心App：`tasks`, `approvals`, `projects`, `users`

### 关键数据模型
```
Task → TaskStageInstance → StageActivity
FlowTemplate → FlowNodeTemplate
ApprovalFlow → ApprovalNode
```

### 当前问题（需解决）
1. tasks模块有独立流程系统，与approvals是两套独立的流程
2. 缺少流程可视化所需的节点记录
3. 缺少超时处理机制

### 交付要求
1. 统一的流程引擎（整合tasks和approvals）
2. 完整的节点活动记录（StageActivity）
3. 转交记录（谁→谁，处理了什么）
4. 超时预警机制
5. 单元测试覆盖

### 工作规范
- 所有代码提交到 `/root/engineering-system/` 
- 使用 git 分支：`alpha/feature-flow-engine`
- 代码风格：Django standard
- 每次完成重要功能后更新 `/.team/tasks/alpha_progress.md`
