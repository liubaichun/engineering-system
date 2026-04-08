# 工程系统设计与代码规范

## 一、现状分析

### 1.1 现有文档结构
```
engineering-system/
├── PROCESS/                          # 流程规范目录
│   ├── pm_review_checklist.md        # PM代码审核检查清单 ✅
│   ├── review_log.md                 # 审核记录
│   ├── deployment_approval.md         # 部署审批
│   ├── deployment_log.md             # 部署记录
│   └── maintenance_log.md            # 维护记录
├── docs/                             # 技术文档
│   ├── OPS_MANUAL.md                 # 运维手册
│   └── React_Native_移动App方案.md   # 移动端方案
└── requirements.txt                  # 依赖清单
```

### 1.2 缺失的规范
| 规范 | 状态 | 说明 |
|------|------|------|
| API接口规范 | ❌ 缺失 | 前后端字段名未统一 |
| 数据模型设计规范 | ❌ 缺失 | 外键 vs 自由文本未明确 |
| 前端API调用规范 | ❌ 缺失 | fetch headers未统一 |
| 数据库设计原则 | ❌ 缺失 | 字段类型选择无标准 |
| 安全设计规范 | ❌ 缺失 | 认证、权限无标准 |

---

## 二、已暴露的问题

### 问题汇总
| 序号 | 问题 | 根因 | 影响 |
|------|------|------|------|
| 1 | 附件上传uploader必填 | 后端serializer要求前端传uploader | 无法上传文件 |
| 2 | 文件下载401 | 前端下载未带Authorization | 无法下载 |
| 3 | 文件预览失败 | 前端直接打开file URL无认证 | 无法预览 |
| 4 | 任务负责人字段不一致 | 前端assignee vs 后端manager | 负责人无法保存 |
| 5 | 负责人显示yangxiaohui | 后端返回username而非中文名 | 体验差 |

### 根因分类
1. **前后端字段名不一致**：serializer字段名与前端表单字段名不匹配
2. **认证头遗漏**：API调用时未统一携带Token
3. **外键滥用**：能用自由文本解决的场景用了外键关联
4. **缺乏API文档**：前端不知道该传什么字段、该用什么格式

---

## 三、解决方案

### 3.1 建立API接口规范

#### 规范要求
```markdown
## API 设计原则

### 认证
- 所有API请求必须携带: `Authorization: Token <token>`
- 前端必须通过 `getAuthHeaders()` 统一获取headers

### 字段命名
- 后端serializer字段名 = 前端表单字段名
- 禁止出现：前端传X、后端期望Y 的情况
- 新增API时，必须同时更新前端调用代码

### 响应格式
```json
{
  "id": 1,
  "field_name": "value",  // snake_case
  "display_name": "显示名"  // 友好显示字段
}
```

### 外键使用原则
| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 需要系统联动的角色 | 外键关联 | 需要查用户表、发通知等 |
| 仅作为信息展示 | 自由文本字段 | 不需要系统联动 |
| 可能的关联/不关联 | 可为空的外键+显示文本 | 灵活适应 |
```

### 3.2 建立数据模型设计规范

```markdown
## 数据模型设计原则

### 字段类型选择

#### 1. 人员/角色字段
- **需要系统联动**（登录、通知、权限）→ 使用 `ForeignKey(User)`
- **仅作为信息记录**（任务负责人、创建人）→ 使用 `CharField(自由文本)`
- **混合场景** → 两者都保留，外键控制联动，文本控制显示

#### 2. 状态/类型字段
- 有限选项 → 使用 `choices` + `CharField`
- 避免用数字代码，易混淆

#### 3. 时间字段
- 精确到日 → `DateField`
- 精确到时间 → `DateTimeField`
- 必填字段 → 不允许 null
- 选填字段 → 允许 null 或 提供默认值

### 设计评审checklist
- [ ] 是否需要关联系统用户？
- [ ] 是否只需要信息展示，不需要系统联动？
- [ ] 前端需要传什么字段？
- [ ] API返回时用什么字段名？
- [ ] 是否有外部系统对接需求？

### 模型变更规范
- 禁止删除已有字段（用deprecated替代）
- 新增字段必须提供默认值或允许null
- 必须同时更新serializer
- 必须更新API文档

### 3.3 前端开发规范

```markdown
## 前端API调用规范

### 必须使用统一认证
```javascript
// 正确
fetch(url, {
  headers: Object.assign({ 'Content-Type': 'application/json' }, getAuthHeaders())
})

// 错误 - 遗漏认证
fetch(url, { method: 'POST', body: formData })
```

### 文件下载/预览
- 禁止直接 `window.open(url)`
- 必须通过fetch + blob方式，带认证头

### 表单字段名
- 必须与后端serializer字段名完全一致
- 新增字段时必须同时更新前后端
```

### 3.4 代码审查扩展清单

```markdown
## 开发自检清单（提交前必须检查）

### 前后端一致性
- [ ] 后端serializer字段名 = 前端表单字段名
- [ ] API响应包含前端需要的显示字段
- [ ] 新增字段已同步更新前后端

### 认证与权限
- [ ] 所有API调用使用getAuthHeaders()
- [ ] 文件下载/预览使用fetch + blob方式
- [ ] 不直接暴露file URL

### 数据库设计
- [ ] 人员字段是否需要外键？还是自由文本？
- [ ] 字段变更是否会影响已有数据？
- [ ] 是否有migration脚本？

### 安全
- [ ] 无硬编码密码/密钥
- [ ] 用户输入已校验
- [ ] SQL注入防护

---

## 四、实施计划

### Phase 1: 立即修复（已完成部分）
- [x] 附件上传uploader修复
- [x] 文件下载401修复
- [x] 文件预览修复
- [x] 任务负责人字段修复
- [ ] **待办**: 全面排查所有前后端不一致问题

### Phase 2: 建立规范文档
- [ ] 建立 `docs/API_DESIGN_STANDARDS.md`
- [ ] 建立 `docs/FRONTEND_DEVELOPMENT_STANDARDS.md`
- [ ] 更新 `PROCESS/pm_review_checklist.md` 加入前后端一致性检查

### Phase 3: 工具化检查
- [ ] 开发前后端字段名一致性检查脚本
- [ ] 自动化API文档生成

---

## 五、待排查清单（全面检查用）

### 需要检查的模块
- [ ] tasks (任务管理) - 已修复
- [ ] attachments (附件管理) - 已修复
- [ ] finance (财务管理)
- [ ] projects (项目管理)
- [ ] approvals (审批流程)
- [ ] inventory (库存管理)
- [ ] equipment (设备管理)
- [ ] users (用户管理)

### 检查要点
1. Serializer字段名 vs 前端表单字段名
2. 文件下载/预览是否带认证
3. 人员字段是否需要改为自由文本
4. 必填字段是否有默认值处理
