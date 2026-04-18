from datetime import datetime
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from knox.models import AuthToken
from .models import User, ApprovalFlow, ApprovalRecord
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
import sys
sys.path.insert(0, '/var/www/engineering_system')
sys.path.insert(0, '/var/www/engineering_green')
try:
    from notifications.feishu_notify import send_approval_notification
except ImportError:
    send_approval_notification = None


class RegisterView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 创建 Knox Token（返回元组：instance, token_string）
        _, token_string = AuthToken.objects.create(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token_string
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """用户登录视图"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        instance, token_string = AuthToken.objects.create(user)
        
        return Response({
            'expiry': instance.expiry,
            'token': token_string,
            'user': UserSerializer(user).data
        })


class MeView(generics.RetrieveUpdateAPIView):
    """当前用户信息视图"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # 已修复：需要登录才能查看
    
    def get_object(self):
        # 优先从Token获取用户（Token认证优先）
        auth_header = self.request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header[6:]
            try:
                token = AuthToken.objects.get(token_key=token_key)
                return token.user
            except AuthToken.DoesNotExist:
                pass
        # 降级：从request.user获取（Session认证）
        if self.request.user and self.request.user.is_authenticated:
            return self.request.user
        return None
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        if user is None:
            return Response({'detail': '未认证'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class LogoutView(generics.GenericAPIView):
    """用户登出视图"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request._auth.delete()
        except Exception:
            pass
        return Response({'status': '登出成功'}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """修改密码视图"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def patch(self, request):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not old_password or not new_password or not new_password_confirm:
            return Response(
                {'detail': '请提供旧密码和新密码'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response(
                {'detail': '旧密码错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != new_password_confirm:
            return Response(
                {'detail': '两次新密码输入不一致'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 6:
            return Response(
                {'detail': '新密码长度不能少于6位'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # 更新 Knox Token
        AuthToken.objects.filter(user=user).delete()
        _, token_string = AuthToken.objects.create(user)
        
        return Response({
            'detail': '密码修改成功',
            'token': token_string
        })


# 简单的路由函数视图
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """用户列表 - 仅管理员和项目经理可访问"""
    if request.user.role not in ('admin', 'pm'):
        return Response({'detail': '权限不足，仅管理员和项目经理可访问'}, status=403)
    users = User.objects.filter(is_active=True)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    """用户详情"""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Phase 2: Registration Approval Flow
# ============================================

class PendingUserListView(APIView):
    """待审核用户列表 - 仅管理员可见"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'admin':
            return Response({'code': 40301, 'message': '仅系统管理员可查看'}, status=status.HTTP_403_FORBIDDEN)
        from users.models import UsersPendingApproval
        users = UsersPendingApproval.objects.filter(status='pending').order_by('-created_at')
        data = [{
            'id': u.id,
            'username': u.username,
            'phone': u.phone or '',
            'role': u.role,
            'email': u.email or '',
            
            'applied_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]
        return Response({'code': 0, 'data': data})


class PendingUserActivateView(APIView):
    """激活用户 - 将待审核用户转为正式用户"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pending_id):
        if request.user.role != 'admin':
            return Response({'code': 40301, 'message': '仅系统管理员可操作'}, status=status.HTTP_403_FORBIDDEN)
        from users.models import UsersPendingApproval
        try:
            pu = UsersPendingApproval.objects.get(id=pending_id, status='pending')
        except UsersPendingApproval.DoesNotExist:
            return Response({'code': 40401, 'message': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 创建正式用户（密码已是哈希值，用create_user会重复加密，故手动创建）
        user = User(
            username=pu.username,
            email=pu.email,
            phone=pu.phone or '',
            role=pu.role,
            is_active=True
        )
        user.password = pu.password  # 直接赋值已哈希的密码，不重复加密
        user.save()
        
        # 更新待审核记录
        pu.status = 'approved'
        pu.reviewed_by = request.user
        pu.reviewed_at = datetime.now()
        pu.save()
        
        return Response({'code': 0, 'message': '用户已激活', 'user_id': user.id})


class PendingUserRejectView(APIView):
    """拒绝用户注册"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pending_id):
        if request.user.role != 'admin':
            return Response({'code': 40301, 'message': '仅系统管理员可操作'}, status=status.HTTP_403_FORBIDDEN)
        remark = request.data.get('remark', '')
        from users.models import UsersPendingApproval
        try:
            pu = UsersPendingApproval.objects.get(id=pending_id, status='pending')
        except UsersPendingApproval.DoesNotExist:
            return Response({'code': 40401, 'message': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        pu.status = 'rejected'
        pu.reviewed_by = request.user
        pu.reviewed_at = datetime.now()
        pu.rejection_reason = remark
        pu.save()
        
        return Response({'code': 0, 'message': '已拒绝'})


# 修改注册视图 - 写入待审核表而非直接创建用户
class RegisterApprovalView(APIView):
    """用户注册（审核制）- 注册后需管理员审批"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone', '')
        role = data.get('role', 'dev')
        real_name = data.get('real_name', '')
        id_card = data.get('id_card', '')
        
        if not username or not password:
            return Response({'code': 40001, 'message': '用户名和密码必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        from users.models import UsersPendingApproval
        # 检查是否已有待审核或已激活
        if User.objects.filter(username=username).exists():
            return Response({'code': 40002, 'message': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
        if UsersPendingApproval.objects.filter(username=username, status='pending').exists():
            return Response({'code': 40003, 'message': '该用户名已在待审核中'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 写入待审核表
        pu = UsersPendingApproval.objects.create(
            username=username,
            password=make_password(password),
            email=data.get('email', username + '@example.com'),
            phone=phone,
            role=role
        )
        
        return Response({
            'code': 0,
            'message': '注册申请已提交，请等待管理员审批',
            'pending_id': pu.id
        })






# Phase 3: Approval Framework (Fixed for existing model)

class ApprovalFlowCreateView(APIView):
    """创建审批流

    POST /api/v1/users/approvals/
    安全修复 TASK-20260413-002：仅允许 admin/pm/finance 角色发起审批流程
    """
    permission_classes = [IsAuthenticated]

    def get_permission_required(self, role):
        """返回该角色发起审批所需的权限"""
        return role in ['admin', 'pm', 'finance']

    def post(self, request):
        # 安全修复 TASK-20260413-002：检查用户是否有发起审批的权限
        if not self.get_permission_required(request.user.role):
            return Response(
                {'detail': '您没有权限发起审批流程，仅限管理员、项目经理和财务人员。'},
                status=status.HTTP_403_FORBIDDEN
            )
        flow_type = request.data.get('flow_type', 'leave')
        target_object_type = request.data.get('target_object_type', '')
        target_object_id = request.data.get('target_object_id')

        approver = self._find_first_approver(request.user, flow_type)
        if approver is None:
            # admin用户无需审批，记录并直接返回成功
            return Response({'code': 0, 'message': '管理员操作已记录（无需审批）'}, status=200)

        # 修复：使用 target_object_id 存储当前审批人ID（模型无 project_id/applicant_role/current_approver_id）
        flow = ApprovalFlow.objects.create(
            applicant=request.user,
            flow_type=flow_type,
            target_object_type=target_object_type,
            target_object_id=approver.id,
            status='pending'
        )

        return Response({
            'code': 0,
            'message': '审批流已创建',
            'flow_id': flow.id,
            'current_approver': approver.username
        })

    def _find_first_approver(self, user, flow_type):
        """查找第一个审批人，admin用户不入审批流"""
        # admin用户不入审批流
        if user.role == 'admin':
            return None
        # 按flow_type路由（预留扩展）
        if flow_type == 'expense':
            return self._find_expense_approver(user)
        if flow_type == 'leave':
            return self._find_leave_approver(user)
        return self._find_default_approver(user)

    def _find_default_approver(self, user):
        """默认审批路由，排除自审批"""
        if user.role == 'pm':
            return User.objects.filter(role='admin', is_active=True).exclude(id=user.id).first()
        if user.role == 'engineer':
            return User.objects.filter(role='pm', is_active=True).exclude(id=user.id).first()
        return User.objects.filter(role='admin', is_active=True).exclude(id=user.id).first()

    def _find_expense_approver(self, user):
        """费用报销审批路由：engineer→pm→admin"""
        if user.role == 'engineer':
            return User.objects.filter(role='pm', is_active=True).exclude(id=user.id).first()
        if user.role == 'pm':
            return User.objects.filter(role='admin', is_active=True).exclude(id=user.id).first()
        return None

    def _find_leave_approver(self, user):
        """请假审批路由：engineer→pm"""
        if user.role == 'engineer':
            return User.objects.filter(role='pm', is_active=True).exclude(id=user.id).first()
        return None


class ApprovalFlowListView(APIView):
    """审批流列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        filter_type = request.query_params.get('filter', 'all')

        # 修复：使用 target_object_id 存储审批人ID
        if filter_type == 'my_pending':
            flows = ApprovalFlow.objects.filter(target_object_id=user.id, status='pending')
        elif filter_type == 'my_applied':
            flows = ApprovalFlow.objects.filter(applicant=user)
        else:
            flows = ApprovalFlow.objects.filter(applicant=user) | ApprovalFlow.objects.filter(target_object_id=user.id)

        flows = flows.distinct().order_by('-created_at')[:50]
        # 预加载审批人（避免N+1查询）
        approver_ids = set(f.target_object_id for f in flows if f.target_object_id)
        approvers = {u.id: u.username for u in User.objects.filter(id__in=approver_ids)} if approver_ids else {}
        data = [{
            'id': f.id,
            'flow_type': f.flow_type,
            'applicant': f.applicant.username,
            'status': f.status,
            'current_approver': approvers.get(f.target_object_id),
            'created_at': f.created_at.isoformat() if f.created_at else None
        } for f in flows]

        return Response({'code': 0, 'data': data})


class ApprovalFlowDetailView(APIView):
    """审批流详情"""
    permission_classes = [IsAuthenticated]

    def get(self, request, flow_id):
        try:
            flow = ApprovalFlow.objects.get(id=flow_id)
        except ApprovalFlow.DoesNotExist:
            return Response({'code': 40401, 'message': '审批流不存在'}, status=404)

        # 修复：使用 target_object_id 获取审批人信息
        approver_username = None
        if flow.target_object_id:
            approver_username = User.objects.filter(id=flow.target_object_id).values_list('username', flat=True).first()

        records = ApprovalRecord.objects.filter(flow_id=flow_id).order_by('created_at')
        data = {
            'id': flow.id,
            'flow_type': flow.flow_type,
            'applicant': flow.applicant.username,
            'status': flow.status,
            'current_approver': approver_username,
            'created_at': flow.created_at.isoformat() if flow.created_at else None,
            'records': [{
                'approver': r.approver.username if r.approver_id else None,
                'action': r.action,
                'remark': r.comment or '',
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in records]
        }
        return Response({'code': 0, 'data': data})


class ApprovalFlowApproveView(APIView):
    """审批通过"""
    permission_classes = [IsAuthenticated]

    def post(self, request, flow_id):
        remark = request.data.get('remark', '')
        try:
            flow = ApprovalFlow.objects.get(id=flow_id, status='pending')
        except ApprovalFlow.DoesNotExist:
            return Response({'code': 40401, 'message': '审批流不存在或已审批'}, status=404)

        # 修复：使用 target_object_id 检查当前审批人
        if flow.target_object_id != request.user.id:
            return Response({'code': 40301, 'message': '您不是当前审批人'}, status=403)

        ApprovalRecord.objects.create(
            flow_id=flow.id,
            approver=request.user,
            approver_role=request.user.role,
            action='approve',
            comment=remark
        )

        flow.status = 'approved'
        flow.save()

        # 发送飞书通知给申请人
        if send_approval_notification:
            send_approval_notification(
                flow.applicant_id,
                request.user.username,
                flow.flow_type,
                'approved',
                remark
            )

        return Response({'code': 0, 'message': '审批已通过'})


class ApprovalFlowRejectView(APIView):
    """审批拒绝"""
    permission_classes = [IsAuthenticated]

    def post(self, request, flow_id):
        remark = request.data.get('remark', '')
        try:
            flow = ApprovalFlow.objects.get(id=flow_id, status='pending')
        except ApprovalFlow.DoesNotExist:
            return Response({'code': 40401, 'message': '审批流不存在或已审批'}, status=404)

        # 修复：使用 target_object_id 检查当前审批人
        if flow.target_object_id != request.user.id:
            return Response({'code': 40301, 'message': '您不是当前审批人'}, status=403)

        ApprovalRecord.objects.create(
            flow_id=flow.id,
            approver=request.user,
            approver_role=request.user.role,
            action='reject',
            comment=remark
        )

        flow.status = 'rejected'
        flow.save()

        # 发送飞书通知给申请人
        if send_approval_notification:
            send_approval_notification(
                flow.applicant_id,
                request.user.username,
                flow.flow_type,
                'rejected',
                remark
            )

        return Response({'code': 0, 'message': '已拒绝'})


class ManagerPendingListView(APIView):
    """经理待审批列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['pm', 'admin']:
            return Response({'code': 40301, 'message': '仅项目经理或管理员可见'}, status=403)

        # 修复：使用 target_object_id 存储审批人ID
        flows = ApprovalFlow.objects.filter(
            target_object_id=request.user.id,
            status='pending'
        ).order_by('-created_at')

        data = [{
            'id': f.id,
            'flow_type': f.flow_type,
            'applicant': f.applicant.username,
            'created_at': f.created_at.isoformat() if f.created_at else None
        } for f in flows]

        return Response({'code': 0, 'data': data})



# ============================================
# Phase 3: Dynamic Menu API
# ============================================

ROLE_MENU = {
    'admin': [
        {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': '控制台', 'url': '/dashboard/'},
        {'id': 'projects', 'icon': 'bi-folder', 'label': '项目管理', 'url': '/projects/'},
        {'id': 'tasks', 'icon': 'bi-list-task', 'label': '任务管理', 'url': '/tasks/'},
        {'id': 'workers', 'icon': 'bi-people', 'label': '施工人员', 'url': '/workers/'},
        {'id': 'customers', 'icon': 'bi-briefcase', 'label': '客户管理', 'url': '/customers/'},
        {'id': 'contracts', 'icon': 'bi-file-earmark-text', 'label': '合同管理', 'url': '/contracts/'},
        {'id': 'quotes', 'icon': 'bi-currency-dollar', 'label': '报价管理', 'url': '/quotes/'},
        {'id': 'finance', 'icon': 'bi-wallet2', 'label': '财务管理', 'url': '/finance/'},
        {'id': 'attendance', 'icon': 'bi-clock', 'label': '考勤管理', 'url': '/attendance/'},
        {'id': 'approval', 'icon': 'bi-check-circle', 'label': '审批管理', 'url': '/approval/'},
        {'id': 'stats', 'icon': 'bi-bar-chart', 'label': '统计报表', 'url': '/stats/'},
        {'id': 'system', 'icon': 'bi-gear', 'label': '系统设置', 'url': '/system/'},
    ],
    'pm': [
        {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': '项目概览', 'url': '/dashboard/'},
        {'id': 'projects', 'icon': 'bi-folder', 'label': '项目概览', 'url': '/projects/'},
        {'id': 'tasks', 'icon': 'bi-list-task', 'label': '进度管理', 'url': '/tasks/'},
        {'id': 'workers', 'icon': 'bi-people', 'label': '人员调度', 'url': '/workers/'},
        {'id': 'attendance_mgr', 'icon': 'bi-calendar-check', 'label': '考勤审批', 'url': '/attendance/manager/'},
        {'id': 'quality', 'icon': 'bi-shield-check', 'label': '质量检查', 'url': '/quality/'},
        {'id': 'finance_pm', 'icon': 'bi-wallet2', 'label': '成本分析', 'url': '/finance/'},
        {'id': 'approval', 'icon': 'bi-check-circle', 'label': '发起申请', 'url': '/approval/'},
        {'id': 'approval_pending', 'icon': 'bi-clipboard-check', 'label': '待我审批', 'url': '/approval/manager_pending/'},
    ],
    'finance': [
        {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': '控制台', 'url': '/dashboard/'},
        {'id': 'contracts', 'icon': 'bi-file-earmark-text', 'label': '合同管理', 'url': '/contracts/'},
        {'id': 'finance_income', 'icon': 'bi-arrow-down-circle', 'label': '收款记录', 'url': '/finance/income/'},
        {'id': 'finance_expense', 'icon': 'bi-arrow-up-circle', 'label': '付款记录', 'url': '/finance/expense/'},
        {'id': 'wages', 'icon': 'bi-cash-stack', 'label': '工资核算', 'url': '/finance/wages/'},
        {'id': 'stats_finance', 'icon': 'bi-bar-chart', 'label': '财务报表', 'url': '/stats/finance/'},
        {'id': 'finance_all', 'icon': 'bi-folder', 'label': '项目成本', 'url': '/finance/'},
        {'id': 'approval', 'icon': 'bi-check-circle', 'label': '审批管理', 'url': '/approval/'},
    ],
    'engineer': [
        {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': '控制台', 'url': '/dashboard/'},
        {'id': 'profile', 'icon': 'bi-person', 'label': '个人信息', 'url': '/profile/'},
        {'id': 'attendance_checkin', 'icon': 'bi-clock', 'label': '考勤打卡', 'url': '/attendance/checkin/'},
        {'id': 'tasks_my', 'icon': 'bi-list-task', 'label': '施工任务', 'url': '/tasks/my_tasks/'},
        {'id': 'safety', 'icon': 'bi-shield', 'label': '安全记录', 'url': '/safety/'},
        {'id': 'wages_my', 'icon': 'bi-cash', 'label': '工资查询', 'url': '/finance/wages/my/'},
        {'id': 'approval_my', 'icon': 'bi-clipboard', 'label': '我的申请', 'url': '/approval/my/'},
    ],
    'business': [
        {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': '控制台', 'url': '/dashboard/'},
        {'id': 'customers', 'icon': 'bi-briefcase', 'label': '客户管理', 'url': '/customers/'},
        {'id': 'opportunities', 'icon': 'bi-star', 'label': '商机跟踪', 'url': '/opportunities/'},
        {'id': 'contracts_new', 'icon': 'bi-file-earmark-plus', 'label': '合同发起', 'url': '/contracts/new/'},
        {'id': 'quotes', 'icon': 'bi-currency-dollar', 'label': '报价管理', 'url': '/quotes/'},
        {'id': 'finance_collection', 'icon': 'bi-arrow-up-circle', 'label': '收款跟进', 'url': '/finance/collection/'},
        {'id': 'projects_cust', 'icon': 'bi-folder', 'label': '客户项目', 'url': '/projects/?filter=my_customers'},
    ],
}


class MenuView(APIView):
    """获取当前用户对应的菜单"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role if request.user else 'admin'
        menu = ROLE_MENU.get(role, ROLE_MENU.get('admin', []))
        return Response({'code': 0, 'data': menu})


# ============================================
# Phase 4: API Permission Decorator
# ============================================

from functools import wraps

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if request.user.role in allowed_roles or request.user.role == 'admin':
                return view_func(self, request, *args, **kwargs)
            return Response({'code': 40301, 'message': '您没有权限访问此功能'}, status=403)
        return wrapper
    return decorator
