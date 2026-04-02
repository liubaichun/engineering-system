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
        _, token_string = AuthToken.objects.create(user=user)
        
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
        instance, token_string = AuthToken.objects.create(user=user)
        
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
        _, token_string = AuthToken.objects.create(user=user)
        
        return Response({
            'detail': '密码修改成功',
            'token': token_string
        })


# 简单的路由函数视图
@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    """用户列表"""
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
            
            'applied_at': u.applied_at.isoformat() if u.applied_at else None
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
        
        # 创建正式用户
        user = User.objects.create_user(
            username=pu.username,
            password=pu.password,
            email=pu.email,
            phone=pu.phone or '',
            role=pu.role,
            is_active=True
        )
        
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
            email=username + '@example.com',  # placeholder
            phone=phone,
            role=role
        )
        
        return Response({
            'code': 0,
            'message': '注册申请已提交，请等待管理员审批',
            'pending_id': pu.id
        })





# Phase 3: Generic Approval Framework

class ApprovalFlowCreateView(APIView):
    """创建审批流"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        flow_type = request.data.get('flow_type')
        project_id = request.data.get('project_id')
        content = request.data.get('content', {})

        if not flow_type:
            return Response({'code': 40001, 'message': 'flow_type必填'}, status=400)

        approver = self._find_first_approver(request.user, project_id, flow_type)
        if not approver:
            return Response({'code': 40002, 'message': '未找到审批人'}, status=400)

        flow = ApprovalFlow.objects.create(
            flow_type=flow_type,
            applicant=request.user,
            applicant_role=request.user.role,
            project_id=project_id,
            content=content,
            current_approver=approver,
            status='pending'
        )

        return Response({
            'code': 0,
            'message': '审批流已创建',
            'flow_id': flow.id,
            'current_approver': approver.username
        })

    def _find_first_approver(self, user, project_id, flow_type):
        if user.role == 'pm':
            return User.objects.filter(role='admin', is_active=True).first()
        if user.role == 'engineer':
            if project_id:
                from projects.models import Project
                project = Project.objects.filter(id=project_id).first()
                if project and project.manager:
                    return project.manager
            return User.objects.filter(role='pm', is_active=True).first()
        return User.objects.filter(role='admin', is_active=True).first()


class ApprovalFlowListView(APIView):
    """审批流列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        filter_type = request.query_params.get('filter', 'all')

        if filter_type == 'my_pending':
            flows = ApprovalFlow.objects.filter(current_approver=user, status='pending')
        elif filter_type == 'my_applied':
            flows = ApprovalFlow.objects.filter(applicant=user)
        else:
            flows = ApprovalFlow.objects.filter(applicant=user) | ApprovalFlow.objects.filter(current_approver=user)

        flows = flows.distinct().order_by('-created_at')[:50]
        data = [{
            'id': f.id,
            'flow_type': f.flow_type,
            'applicant': f.applicant.username,
            'applicant_role': f.applicant_role,
            'project_id': f.project_id,
            'status': f.status,
            'current_approver': f.current_approver.username if f.current_approver else None,
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

        records = ApprovalRecord.objects.filter(flow=flow).order_by('created_at')
        data = {
            'id': flow.id,
            'flow_type': flow.flow_type,
            'applicant': flow.applicant.username,
            'applicant_role': flow.applicant_role,
            'project_id': flow.project_id,
            'content': flow.content,
            'status': flow.status,
            'current_approver': flow.current_approver.username if flow.current_approver else None,
            'created_at': flow.created_at.isoformat() if flow.created_at else None,
            'records': [{
                'approver': r.approver.username if r.approver else None,
                'action': r.action,
                'remark': r.remark,
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

        if flow.current_approver != request.user:
            return Response({'code': 40301, 'message': '您不是当前审批人'}, status=403)

        ApprovalRecord.objects.create(
            flow=flow,
            approver=request.user,
            approver_role=request.user.role,
            action='approve',
            remark=remark
        )

        flow.status = 'approved'
        flow.save()

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

        if flow.current_approver != request.user:
            return Response({'code': 40301, 'message': '您不是当前审批人'}, status=403)

        ApprovalRecord.objects.create(
            flow=flow,
            approver=request.user,
            approver_role=request.user.role,
            action='reject',
            remark=remark
        )

        flow.status = 'rejected'
        flow.save()

        return Response({'code': 0, 'message': '已拒绝'})


class ManagerPendingListView(APIView):
    """经理待审批列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['pm', 'admin']:
            return Response({'code': 40301, 'message': '仅项目经理或管理员可见'}, status=403)

        flows = ApprovalFlow.objects.filter(
            current_approver=request.user,
            status='pending'
        ).order_by('-created_at')

        data = [{
            'id': f.id,
            'flow_type': f.flow_type,
            'applicant': f.applicant.username,
            'applicant_role': f.applicant_role,
            'project_id': f.project_id,
            'created_at': f.created_at.isoformat() if f.created_at else None
        } for f in flows]

        return Response({'code': 0, 'data': data})

