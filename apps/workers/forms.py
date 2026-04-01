# ============================================================
# 5. 前端表单字段参考 (forms.py)
# ============================================================
# 说明：以下为前端 Vue/React 页面所需字段的完整定义
# 可直接对应到 Element Plus / Ant Design / Tailwind 表单组件
# 与后端 Model/Serializer 字段一一对应

# ============================================================
# 人员档案 - 前端表单字段
# ============================================================
WORKER_FORM_FIELDS = {
    # ----- 基本信息 -----
    "name": {
        "label": "姓名",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入姓名",
        "rules": [{"required": True, "message": "请输入姓名", "trigger": "blur"}],
        "span": 12,       #栅格占位（12/24 = 半宽）
    },
    "id_card": {
        "label": "身份证号",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入18位身份证号",
        "rules": [
            {"required": True, "message": "请输入身份证号", "trigger": "blur"},
            {"pattern": r"^\d{17}[\dXx]$", "message": "身份证号格式不正确", "trigger": "blur"},
        ],
        "span": 12,
    },
    "phone": {
        "label": "手机号",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入手机号",
        "rules": [
            {"required": True, "message": "请输入手机号", "trigger": "blur"},
            {"pattern": r"^1[3-9]\d{9}$", "message": "手机号格式不正确", "trigger": "blur"},
        ],
        "span": 12,
    },

    # ----- 务工信息 -----
    "work_type": {
        "label": "工种",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择工种",
        "options": [
            {"value": "rebar",      "label": "钢筋工"},
            {"value": "carpenter",  "label": "木工"},
            {"value": "concrete",   "label": "混凝土工"},
            {"value": "plumber",    "label": "水电工"},
            {"value": "painter",    "label": "油漆工"},
            {"value": "scaffolder", "label": "架子工"},
            {"value": "laborer",    "label": "杂工"},
        ],
        "rules": [{"required": True, "message": "请选择工种", "trigger": "change"}],
        "span": 12,
    },
    "skill_level": {
        "label": "技能等级",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择技能等级（可选）",
        "options": [
            {"value": "junior",        "label": "初级"},
            {"value": "intermediate",  "label": "中级"},
            {"value": "senior",         "label": "高级"},
            {"value": "master",         "label": "技师"},
        ],
        "required": False,
        "span": 12,
    },

    # ----- 组织归属 -----
    "group": {
        "label": "所属班组",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择班组（可选）",
        "remote": "/api/v1/groups/",    # 远程数据源
        "remote_prop": {"label": "name", "value": "id"},
        "filterable": True,
        "clearable": True,
        "required": False,
        "span": 12,
    },

    # ----- 状态 & 日期 -----
    "status": {
        "label": "状态",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择状态",
        "options": [
            {"value": "active",   "label": "在职"},
            {"value": "inactive", "label": "离职"},
            {"value": "paused",   "label": "暂停"},
        ],
        "rules": [{"required": True, "message": "请选择状态", "trigger": "change"}],
        "span": 12,
        "default": "active",
    },
    "entry_date": {
        "label": "入场日期",
        "type": "date",
        "component": "el-date-picker",
        "placeholder": "请选择入场日期",
        "value_format": "YYYY-MM-DD",
        "required": False,
        "span": 12,
    },
    "leave_date": {
        "label": "退场日期",
        "type": "date",
        "component": "el-date-picker",
        "placeholder": "请选择退场日期",
        "value_format": "YYYY-MM-DD",
        "required": False,
        "span": 12,
        "dependencies": ["entry_date"],  # 依赖入场日期，需校验 > entry_date
    },

    # ----- 扩展信息 -----
    "emergency_contact": {
        "label": "紧急联系人",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入紧急联系人",
        "required": False,
        "span": 12,
    },
    "emergency_phone": {
        "label": "紧急联系电话",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入紧急联系电话",
        "required": False,
        "span": 12,
    },
    "health_cert": {
        "label": "健康证号",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入健康证号",
        "required": False,
        "span": 12,
    },
    "safety_cert": {
        "label": "安全证号",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入安全证号",
        "required": False,
        "span": 12,
    },
    "remark": {
        "label": "备注",
        "type": "textarea",
        "component": "el-input",
        "placeholder": "备注信息（选填）",
        "rows": 3,
        "required": False,
        "span": 24,
    },
}

# ============================================================
# 人员列表页 - 表格列定义
# ============================================================
WORKER_TABLE_COLUMNS = [
    {"prop": "name",            "label": "姓名",           "width": 100},
    {"prop": "phone",           "label": "手机号",         "width": 130},
    {"prop": "work_type_display","label": "工种",          "width": 100},
    {"prop": "skill_level_display","label": "技能等级",   "width": 90},
    {"prop": "group_name",      "label": "所属班组",       "width": 120},
    {"prop": "status_display",  "label": "状态",          "width": 80,
     "tag": True,
     "tag_type_map": {"在职": "success", "离职": "info", "暂停": "warning"}},
    {"prop": "entry_date",      "label": "入场日期",       "width": 120},
    {"prop": "actions",         "label": "操作",          "width": 160,
     "buttons": ["edit", "delete"]},
]

# ============================================================
# 班组管理 - 前端表单字段
# ============================================================
GROUP_FORM_FIELDS = {
    "name": {
        "label": "班组名称",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入班组名称",
        "rules": [{"required": True, "message": "请输入班组名称", "trigger": "blur"}],
        "span": 12,
    },
    "leader": {
        "label": "班组长",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择班组长",
        "remote": "/api/v1/workers/",   # 筛选在职人员
        "remote_prop": {"label": "name", "value": "id"},
        "remote_query": {"status": "active"},
        "filterable": True,
        "clearable": True,
        "required": False,
        "span": 12,
    },
    "phone": {
        "label": "联系电话",
        "type": "input",
        "component": "el-input",
        "placeholder": "请输入联系电话",
        "rules": [
            # 国内手机号或固话
            {"pattern": r"^1[3-9]\d{9}$", "message": "手机号格式不正确", "trigger": "blur"},
        ],
        "span": 12,
    },
    "project": {
        "label": "当前项目",
        "type": "select",
        "component": "el-select",
        "placeholder": "请选择当前项目（可选）",
        "remote": "/api/v1/projects/",
        "remote_prop": {"label": "name", "value": "id"},
        "filterable": True,
        "clearable": True,
        "required": False,
        "span": 12,
    },
    "remark": {
        "label": "备注",
        "type": "textarea",
        "component": "el-input",
        "placeholder": "备注信息（选填）",
        "rows": 3,
        "required": False,
        "span": 24,
    },
}

# ============================================================
# 班组列表页 - 表格列定义
# ============================================================
GROUP_TABLE_COLUMNS = [
    {"prop": "name",       "label": "班组名称", "width": 160},
    {"prop": "leader_name","label": "班组长",   "width": 100},
    {"prop": "phone",      "label": "联系电话", "width": 130},
    {"prop": "project_name","label": "当前项目", "width": 180},
    {"prop": "worker_count","label": "人数",    "width": 80},
    {"prop": "actions",    "label": "操作",     "width": 160,
     "buttons": ["detail", "edit", "delete"]},
]

# ============================================================
# 页面路由配置（前端 Vue Router）
# ============================================================
FRONTEND_ROUTES = [
    {"path": "/workers/",           "name": "WorkerList",   "component": "WorkerListView",   "meta": {"title": "人员列表"}},
    {"path": "/workers/add/",        "name": "WorkerAdd",    "component": "WorkerFormView",   "meta": {"title": "新增人员"}},
    {"path": "/workers/:id/edit/",   "name": "WorkerEdit",   "component": "WorkerFormView",   "meta": {"title": "编辑人员"}},
    {"path": "/workers/:id/",        "name": "WorkerDetail", "component": "WorkerDetailView", "meta": {"title": "人员详情"}},

    {"path": "/groups/",             "name": "GroupList",    "name": "GroupList",   "component": "GroupListView",   "meta": {"title": "班组列表"}},
    {"path": "/groups/add/",         "name": "GroupAdd",     "component": "GroupFormView",    "meta": {"title": "新增班组"}},
    {"path": "/groups/:id/edit/",    "name": "GroupEdit",    "component": "GroupFormView",    "meta": {"title": "编辑班组"}},
    {"path": "/groups/:id/",         "name": "GroupDetail", "component": "GroupDetailView", "meta": {"title": "班组详情"}},
]
