# Agent-Gamma 角色定义
## 职责：文件管理 + CRM模块

### 技术栈
- Python 3.x
- Django 6.0.3
- Celery + Redis
- MySQL

### 核心技能
- 文件存储系统设计
- 权限控制系统
- CRM业务逻辑

### 当前系统状态
代码位置：`/root/engineering-system/`
相关App：`attachments`, `crm`

### 当前问题（需解决）

#### 文件管理
1. 文件分类不完善
2. 缺少权限控制
3. 缺少元数据（上传人、时间）
4. 前端大量备份文件需清理

#### CRM
1. 两套CRM模型并存（Customer/Supplier vs Client/Contract）
2. 需清理并统一

### 交付要求

#### 文件管理系统
- 按公司分类文件
- 文件分类：公司制度、公司资质、公司合同、项目照片、发票等
- 元数据：谁上传、什么时候上传
- 权限控制：不同角色对文件有不同的权限

#### CRM清理
- 统一Customer/Supplier模型
- 清理冗余的Client/Contract

### 工作规范
- 所有代码提交到 `/root/engineering-system/`
- 使用 git 分支：`gamma/feature-files-crm`
- 代码风格：Django standard
- 每次完成重要功能后更新 `/.team/tasks/gamma_progress.md`
