from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from knox.models import AuthToken
from .models import User
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
