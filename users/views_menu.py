"""
动态菜单API - Phase 3
GET /api/v1/auth/menu/ - 返回当前用户角色对应的菜单列表
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


MENUS = {
    'admin': [
        {'group': '系统管理', 'items': [
            {'icon': 'bi-gear', 'label': '系统配置', 'url': '/system/'},
            {'icon': 'bi-people', 'label': '用户管理', 'url': '/users/'},
            {'icon': 'bi-shield', 'label': '角色管理', 'url': '/roles/'},
            {'icon': 'bi-bar-chart', 'label': '报表中心', 'url': '/reports/'},
            {'icon': 'bi-journal', 'label': '审计日志', 'url': '/operation_logs/'},
        ]},
        {'group': '审批管理', 'items': [
            {'icon': 'bi-person-check', 'label': '用户注册审批', 'url': '/pending_users/'},
            {'icon': 'bi-check-circle', 'label': '考勤审批', 'url': '/approvals/'},
            {'icon': 'bi-wallet', 'label': '费用审批', 'url': '/approvals/?type=expense'},
        ]},
        {'group': '业务管理', 'items': [
            {'icon': 'bi-folder', 'label': '项目管理', 'url': '/projects/'},
            {'icon': 'bi-kanban', 'label': '任务看板', 'url': '/tasks/'},
            {'icon': 'bi-wallet', 'label': '财务管理', 'url': '/finance/'},
            {'icon': 'bi-file-earmark', 'label': '文件管理', 'url': '/files/'},
        ]},
    ],
    'pm': [
        {'group': '项目管理', 'items': [
            {'icon': 'bi-grid', 'label': '项目概览', 'url': '/dashboard/'},
            {'icon': 'bi-folder', 'label': '项目列表', 'url': '/projects/'},
            {'icon': 'bi-kanban', 'label': '任务看板', 'url': '/tasks/'},
        ]},
        {'group': '人员调度', 'items': [
            {'icon': 'bi-people', 'label': '施工人员', 'url': '/workers/'},
            {'icon': 'bi-qr-code-scan', 'label': '考勤打卡', 'url': '/attendance/'},
        ]},
        {'group': '审批管理', 'items': [
            {'icon': 'bi-check-circle', 'label': '考勤审批', 'url': '/approvals/'},
            {'icon': 'bi-wallet', 'label': '费用审批', 'url': '/approvals/?type=expense'},
        ]},
        {'group': '质量成本', 'items': [
            {'icon': 'bi-clipboard-check', 'label': '质量检查', 'url': '/quality/'},
            {'icon': 'bi-graph-up', 'label': '成本分析', 'url': '/cost/'},
        ]},
    ],
    'finance': [
        {'group': '合同管理', 'items': [
            {'icon': 'bi-file-text', 'label': '合同列表', 'url': '/contracts/'},
            {'icon': 'bi-folder', 'label': '合同模板', 'url': '/contract-templates/'},
        ]},
        {'group': '收支管理', 'items': [
            {'icon': 'bi-arrow-down-circle', 'label': '收款记录', 'url': '/finance/income/'},
            {'icon': 'bi-arrow-up-circle', 'label': '付款记录', 'url': '/finance/expense/'},
        ]},
        {'group': '工资核算', 'items': [
            {'icon': 'bi-cash-stack', 'label': '工资发放', 'url': '/payroll/'},
            {'icon': 'bi-receipt', 'label': '工资条', 'url': '/payroll/slips/'},
        ]},
        {'group': '财务报表', 'items': [
            {'icon': 'bi-bar-chart', 'label': '收支报表', 'url': '/reports/finance/'},
            {'icon': 'bi-file-earmark-spreadsheet', 'label': '导出报表', 'url': '/reports/export/'},
        ]},
    ],
    'engineer': [
        {'group': '个人信息', 'items': [
            {'icon': 'bi-person', 'label': '我的信息', 'url': '/profile/'},
            {'icon': 'bi-telephone', 'label': '联系方式', 'url': '/profile/contact/'},
        ]},
        {'group': '考勤打卡', 'items': [
            {'icon': 'bi-qr-code-scan', 'label': '立即打卡', 'url': '/attendance/signin/'},
            {'icon': 'bi-clock-history', 'label': '打卡记录', 'url': '/attendance/records/'},
        ]},
        {'group': '施工任务', 'items': [
            {'icon': 'bi-kanban', 'label': '我的任务', 'url': '/tasks/my/'},
            {'icon': 'bi-check2-square', 'label': '任务完成', 'url': '/tasks/complete/'},
        ]},
        {'group': '工资查询', 'items': [
            {'icon': 'bi-wallet', 'label': '工资明细', 'url': '/payroll/slip/'},
        ]},
    ],
    'business': [
        {'group': '客户管理', 'items': [
            {'icon': 'bi-building', 'label': '客户列表', 'url': '/customers/'},
            {'icon': 'bi-person-plus', 'label': '新增客户', 'url': '/customers/add/'},
        ]},
        {'group': '商机跟踪', 'items': [
            {'icon': 'bi-lightning', 'label': '商机列表', 'url': '/opportunities/'},
            {'icon': 'bi-chat-left-dots', 'label': '跟进记录', 'url': '/opportunities/follow/'},
        ]},
        {'group': '合同管理', 'items': [
            {'icon': 'bi-file-text', 'label': '合同列表', 'url': '/contracts/'},
            {'icon': 'bi-file-plus', 'label': '新建合同', 'url': '/contracts/add/'},
        ]},
        {'group': '报价管理', 'items': [
            {'icon': 'bi-file-earmark-dollar', 'label': '报价单', 'url': '/quotes/'},
            {'icon': 'bi-currency-dollar', 'label': '收款跟进', 'url': '/quotes/payment/'},
        ]},
    ],
}


class AuthMenuView(APIView):
    """
    GET /api/v1/auth/menu/
    返回当前用户角色对应的菜单列表
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role or 'engineer'
        menu = MENUS.get(role, MENUS.get('engineer', []))
        return Response({
            'role': role,
            'menu': menu,
            'username': request.user.username,
        })


# ── Phase 4: API权限拦截 ──────────────────────────────────────────────

from functools import wraps
from rest_framework import status
from rest_framework.response import Response


def role_required(*allowed_roles):
    """
    装饰器: @role_required('admin', 'pm')
    仅允许指定角色的用户访问
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return Response(
                    {'detail': f'权限不足，需要角色: {", ".join(allowed_roles)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin:
    """
    Mixin: 为ViewSet提供角色检查
    用法: class MyViewSet(RoleRequiredMixin, viewsets.ModelViewSet):
        required_roles = ['admin', 'pm']
    """
    required_roles = []

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # admin 无限制
        if user.role == 'admin':
            return queryset

        # 检查角色
        if self.required_roles and user.role not in self.required_roles:
            return queryset.none()

        return queryset
