from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from knox.models import AuthToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

User = get_user_model()

LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCK_MINUTES = 15


class RegisterView(generics.CreateAPIView):
    """用户注册"""
    permission_classes = [AllowAny]
    throttle_classes = []  # Rate limited at settings level
    authentication_classes = []
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, token_string = AuthToken.objects.create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token_string
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """用户登录"""
    permission_classes = [AllowAny]
    throttle_classes = []  # Rate limited at settings level

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

        # 检查是否被锁定
        if user.login_lock_until and user.login_lock_until > timezone.now():
            remaining = (user.login_lock_until - timezone.now()).seconds // 60 + 1
            return Response({'error': f'账户已锁定，请{remaining}分钟后重试'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if not user.check_password(password):
            user.login_fail_count += 1
            if user.login_fail_count >= LOGIN_MAX_ATTEMPTS:
                user.login_lock_until = timezone.now() + timedelta(minutes=LOGIN_LOCK_MINUTES)
                user.save()
                return Response({'error': '登录失败次数过多，账户已锁定15分钟'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            user.save()
            return Response({'error': f'用户名或密码错误，剩余{LOGIN_MAX_ATTEMPTS - user.login_fail_count}次机会'}, status=status.HTTP_401_UNAUTHORIZED)

        # 登录成功，重置失败计数
        user.login_fail_count = 0
        user.login_lock_until = None
        user.save()
        instance, token_string = AuthToken.objects.create(user=user)
        return Response({
            'expiry': instance.expiry,
            'token': token_string,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """用户登出"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request._auth.delete()
        except Exception:
            pass
        return Response({'message': '登出成功'})


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """当前用户信息"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
