# GitHub 分支保护设置指南

## 需要手动在GitHub网页上配置

由于分支保护需要GitHub仓库管理员权限，请按以下步骤操作：

---

## 步骤1：配置分支保护

1. 打开 GitHub 仓库：https://github.com/liubaichun/engineering-system
2. 点击 **Settings**（设置）
3. 左侧菜单选择 **Branches**（分支）
4. 点击 **Add branch protection rule**（添加分支保护规则）
5. 配置如下：

### 分支保护规则设置

| 设置项 | 值 |
|--------|-----|
| **Branch name pattern** | `main` 或 `master`（取决于你的默认分支） |
| ✅ Require a pull request before merging | 勾选 |
| ✅ Require approvals | 勾选，设置为 **1** |
| ✅ Dismiss stale approvals when new commits are pushed | 勾选 |
| ✅ Require approval from code owners | 可选 |
| ✅ Require status checks to pass before merging | 勾选 |
| ✅ Required status checks | 选择 `ci.yml` (lint, test) |
| ✅ Do not allow bypassing the above settings | 勾选（管理员也不能绕过） |

---

## 步骤2：配置GitHub Actions权限

1. Settings → Actions → General
2. 选择 **Read and write permissions**
3. 保存

---

## 步骤3：启用GitHub Actions（如果还没启用）

1. 点击仓库的 **Actions** 标签
2. 如果提示启用，点击 **I understand my workflows, go ahead and enable them**

---

## 验证

配置完成后：
1. 尝试直接push到main分支 → 应该被拒绝
2. 创建PR → 应该触发CI检查
3. CI通过后 → 需要至少1人Approve才能合并

---

## 注意事项

- 分支保护配置后，合并PR需要至少1人审核
- GitHub Actions有免费额度（2000分钟/月）
- 所有配置都在 `.github/workflows/ci.yml`
