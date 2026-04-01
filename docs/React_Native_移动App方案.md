# React Native 移动App设计方案

**版本：** v1.0
**日期：** 2026-03-30
**作者：** UX-001
**目标上线：** Q3 2026

---

## 一、技术选型

### 推荐：React Native + Expo

| 维度 | React Native + Expo | Flutter | 结论 |
|------|---------------------|---------|------|
| 开发效率 | ⭐⭐⭐⭐⭐ 热更新快 | ⭐⭐⭐⭐ | RN更适合现有团队 |
| 地图生态 | react-native-maps (Google/Apple) | Google Maps插件成熟 | 持平 |
| GPS/定位 | expo-location | geolocator插件 | Expo更无缝 |
| DRF对接 | fetch/axios | http/dio | 持平 |
| 学习曲线 | React团队上手快 | 需学Dart | RN胜出 |
| 团队现状 | 前端Bootstrap+JS | 无 | RN复用知识 |

**技术栈：**
```json
{
  "framework": "Expo SDK 52",
  "language": "TypeScript",
  "navigation": "Expo Router (file-based)",
  "state": "Zustand (lightweight) + TanStack Query",
  "maps": "react-native-maps",
  "location": "expo-location",
  "camera": "expo-camera (二维码)",
  "http": "axios",
  "storage": "expo-secure-store (token)"
}
```

### 不选Flutter原因
- 团队无Dart经验，学习成本2-3个月
- 装修项目管理系统不值得此投入

---

## 二、核心功能设计

### 2.1 功能矩阵

| 功能 | 优先级 | 描述 |
|------|--------|------|
| GPS智能签到 | P0 | 自动定位+拍照+时间戳 |
| 项目地图总览 | P0 | Leaflet地图+工人位置 |
| 任务列表 | P1 | 我的任务、状态更新 |
| 消息通知 | P1 | Push通知+站内消息 |
| 考勤记录 | P1 | 历史考勤打卡记录 |
| 个人信息 | P2 | 账户设置、头像 |

### 2.2 页面结构

```
App
├── (tabs)                    # 底部Tab导航
│   ├── index.tsx             # 首页：快捷签到 + 今日任务
│   ├── projects.tsx          # 项目列表
│   ├── tasks.tsx             # 我的任务
│   ├── checkin.tsx           # 考勤打卡
│   └── profile.tsx            # 我的
│
├── project/[id].tsx          # 项目详情
├── task/[id].tsx             # 任务详情
├── map.tsx                   # 全屏地图
└── qr-scan.tsx               # 扫码页面
```

### 2.3 核心页面设计

#### 首页（index.tsx）
```
┌─────────────────────────┐
│  👋 张工，今天是3月30日   │  ← 问候+日期
├─────────────────────────┤
│  ┌─────────────────────┐ │
│  │  📍 快捷打卡         │ │  ← 一键签到入口
│  │  [当前位置] 点击签到  │ │
│  │  误差: ±15米        │ │
│  └─────────────────────┘ │
├─────────────────────────┤
│  今日任务 (3)            │
│  ┌───────┬───────┬─────┐│
│  │ 🔴    │ 🟡    │ 🟢  ││  ← 任务状态速览
│  │ 1     │ 1     │ 1   ││
│  └───────┴───────┴─────┘│
├─────────────────────────┤
│  待办事项                │
│  • 3号楼层施工检查  →   │  ← 点击跳转详情
│  • 材料进场验收      →   │
└─────────────────────────┘
```

#### 考勤打卡（checkin.tsx）
```
┌─────────────────────────┐
│  📍 当前定位             │
│  ┌─────────────────────┐ │
│  │   [MAP PLACEHOLDER]  │ │  ← 实时地图
│  │        📍            │ │  ← 当前位置
│  │   [项目A] 23米       │ │  ← 最近项目+距离
│  └─────────────────────┘ │
│                          │
│  定位精度: ±15米 ✅      │
│  GPS信号: 强 ✅          │
│                          │
│  [ 📷 拍照打卡 ]         │  ← 拍照按钮
│                          │
│  [ ✅ 确认签到 ]          │  ← 提交按钮
└─────────────────────────┘
```

---

## 三、与现有DRF API对接

### 3.1 API适配层设计

```typescript
// lib/api.ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const BASE_URL = 'https://43.156.139.37/api/v1';

const api = axios.create({ baseURL: BASE_URL });

// 请求拦截：注入token
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('auth_token');
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

// 响应拦截：处理401
api.interceptors.response.use(
  (r) => r,
  async (err) => {
    if (err.response?.status === 401) {
      await SecureStore.deleteItemAsync('auth_token');
      // 跳转登录
    }
    return Promise.reject(err);
  }
);

export default api;

// ============ 核心接口 ============

// POST /api/v1/checkin/  签到
export const postCheckin = (data: {
  latitude: number;
  longitude: number;
  photo_base64?: string;
  project_id?: number;
  note?: string;
}) => api.post('/checkin/', data);

// GET /api/v1/workers/me/  我的信息
export const getMyProfile = () => api.get('/workers/me/');

// GET /api/v1/projects/  项目列表
export const getProjects = (params?: { status?: string }) =>
  api.get('/projects/', { params });

// GET /api/v1/tasks/my/  我的任务
export const getMyTasks = () => api.get('/tasks/my/');

// GET /api/v1/notifications/  通知
export const getNotifications = () => api.get('/notifications/');
```

### 3.2 签到API增强需求

**当前API缺少字段：**
```python
# 建议新增 /api/v1/checkin/ 响应
{
    "id": 1,
    "worker": 1,
    "project": 3,
    "latitude": 31.2304,
    "longitude": 121.4737,
    "accuracy": 15.0,        # 新增：GPS精度（米）
    "photo_url": null,       # 新增：拍照图片URL
    "checkin_time": "2026-03-30T08:30:00Z",
    "is_valid": true,        # 新增：是否在允许范围内
    "distance_from_project": 23  # 新增：距项目距离
}
```

---

## 四、UI组件设计

### 4.1 设计系统

```typescript
// theme/colors.ts
export const colors = {
  primary: '#0d6efd',
  success: '#198754',
  warning: '#ffc107',
  danger: '#dc3545',
  // 沿用现有Bootstrap色彩体系
  sidebarBg: '#1a1a2e',
  cardBg: '#ffffff',
  pageBg: '#f0f2f5',
};

// theme/spacing.ts
export const spacing = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
};

// theme/typography.ts
export const typography = {
  h1: { fontSize: 24, fontWeight: '700' as const },
  h2: { fontSize: 20, fontWeight: '600' as const },
  body: { fontSize: 16, fontWeight: '400' as const },
  caption: { fontSize: 12, color: '#6c757d' },
};
```

### 4.2 关键组件

| 组件 | 状态 | 说明 |
|------|------|------|
| CheckinCard | 已设计 | 地图+定位+拍照 |
| TaskListItem | 已设计 | 状态徽章+进度 |
| ProjectCard | 已设计 | 封面+状态+成员 |
| StatusBadge | 已设计 | 红/黄/绿状态 |
| BottomTabNav | 已设计 | 5Tab，iOS风格 |
| GpsIndicator | 已设计 | 信号强度+误差 |

---

## 五、实施路线图

### Q3 里程碑（7-9月）

```
July (第1-4周)
├── Week 1-2: 环境搭建
│   ├── Expo项目初始化
│   ├── TypeScript配置
│   ├── Navigation (Expo Router)
│   └── Design System基础组件
├── Week 3-4: 认证+首页
│   ├── Token存储 (expo-secure-store)
│   ├── 登录/注册页
│   ├── 首页布局
│   └── API适配层
│
August (第5-8周)
├── Week 5-6: 核心功能
│   ├── GPS定位 (expo-location)
│   ├── 地图集成 (react-native-maps)
│   └── 签到功能
├── Week 7-8: 项目+任务
│   ├── 项目列表/详情
│   ├── 任务列表/更新
│   └── 消息通知
│
September (第9-12周)
├── Week 9-10: 完善+测试
│   ├── 个人中心
│   ├── Push通知
│   └── 集成测试
├── Week 11: 内部测试
│   └── 10人小规模试用
└── Week 12: 上线准备
    ├── App Store / 豌豆荚 / 应用宝
    └── 后端API适配
```

### 关键检查点

| 阶段 | 目标 | 验收标准 |
|------|------|----------|
| MVP签到 | Week 6末 | 能完成一次完整签到 |
| 地图+GPS | Week 8末 | 地图显示+位置准确 |
| 完整App | Week 10末 | 5个Tab全部可用 |
| 试运行 | Week 12末 | 10人7天使用无崩溃 |

---

## 六、工作量估算

### 人力估算（单人开发）

| 模块 | 工作量 | 说明 |
|------|--------|------|
| 环境+架构 | 3天 | 项目搭建、设计系统、导航 |
| 认证+API层 | 2天 | Token管理、API适配 |
| 首页+Tab导航 | 2天 | 布局、快捷签到入口 |
| GPS定位 | 2天 | expo-location、误差处理 |
| 地图功能 | 3天 | react-native-maps、项目标记 |
| 签到流程 | 3天 | 拍照+提交+反馈 |
| 项目模块 | 2天 | 列表+详情 |
| 任务模块 | 2天 | 列表+状态更新 |
| 消息通知 | 2天 | 轮询+展示 |
| 个人中心 | 1天 | 账户、设置 |
| 测试+修复 | 3天 | 跨设备测试 |
| **合计** | **25天** | 约5周（1人全职） |

### 团队配置（推荐2人）

| 角色 | 工作 |
|------|------|
| 前端（RN开发） | 主攻App开发 |
| 后端（DRF开发） | API适配+地图服务 |

---

## 七、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| GPS精度不足 | 签到位置偏差大 | 显示误差范围，允许±50m |
| 离线无法签到 | 功能失效 | 缓存+离线队列 |
| API兼容 | 字段缺失 | 后端提前适配（DevOps协调） |
| App Store审核 | 上线延迟 | 提前准备资质材料 |
| 跨城市GPS差异 | 信号弱 | 降级到基站定位 |

---

## 八、文件路径

**本文档：** `/var/www/engineering_system/docs/React_Native_移动App方案.md`

**后续交付物：**
- `/var/www/engineering_system/docs/RN_App_原型设计.xd` (Figma导出)
- `/var/www/engineering_system/docs/RN_App_接口文档.md`
- `/var/www/engineering_system/docs/RN_App_测试用例.md`
