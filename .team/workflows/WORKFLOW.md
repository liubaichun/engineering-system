# 工作流程管理

## 任务分配流程

```
1. 我（技术负责人）拆分任务
       ↓
2. 发布任务到 /.team/tasks/
       ↓
3. 启动对应子agent执行
       ↓
4. 子agent完成 → 更新进度报告
       ↓
5. 我整合代码到主分支
       ↓
6. 测试验证
```

## 代码整合流程

```
subagent 完成代码
       ↓
提交到自己的分支 (e.g., alpha/feature-flow-engine)
       ↓
向我报告完成
       ↓
我 review 并合并到主分支
       ↓
通知相关agent同步
```

## 沟通机制

### 定期同步（每个任务周期）
- 子agent完成阶段工作后更新：`/.team/tasks/[name]_progress.md`
- 我定期检查进度
- 阻塞时子agent通过输出向我求助

### 紧急情况
- 重大bug：立即报告
- 架构变更：立即报告
- 超过预计时间：提前报告

## Git 工作流程

```
master (稳定分支)
  ↑
  │ (我合并)
  │
alpha/feature-flow-engine  (Alpha工作分支)
beta/feature-finance       (Beta工作分支)
gamma/feature-files-crm    (Gamma工作分支)
delta/feature-frontend     (Delta工作分支)
```

## 任务优先级

P0：任务流程可视化（Alpha）
P1：工资系统（Beta）
P2：文件管理（Gamma）
P3：CRM清理（Gamma）
P4：前端优化（Delta）
