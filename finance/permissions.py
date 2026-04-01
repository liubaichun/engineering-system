from rest_framework.permissions import BasePermission


class IsFinanceOnly(BasePermission):
    """
    自定义权限：只允许 admin 和 finance 角色访问财务模块
    """
    message = "您没有权限访问财务模块，仅限管理员和财务人员。"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'finance']
