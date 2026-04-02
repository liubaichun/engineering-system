from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8, label='密码')
    password_confirm = serializers.CharField(write_only=True, label='确认密码')
    
    class Meta:
        model = User
        # 安全修复：移除role字段，新用户默认注册为dev角色
        # 管理员角色只能由admin后台创建，禁止自助注册
        fields = ['username', 'email', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': False},
        }
    
    def validate_password(self, value):
        """密码复杂度校验：至少8字符，大小写字母+数字"""
        if len(value) < 8:
            raise serializers.ValidationError('密码至少需要8个字符')
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in value):
            raise serializers.ValidationError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError('密码必须包含至少一个数字')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': '两次密码输入不一致'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        # 安全修复：强制设置默认角色为dev，禁止注册为admin或其他高权限角色
        # 显式忽略前端传入的role参数，确保安全
        validated_data.pop('role', None)
        validated_data['role'] = 'dev'
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField(label='用户名')
    password = serializers.CharField(label='密码', write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 统一错误信息，不区分用户不存在和密码错误
            raise serializers.ValidationError('用户名或密码错误')

        # 检查用户是否被锁定
        if user.is_locked():
            remaining_time = (user.lock_until - timezone.now()).seconds // 60
            raise serializers.ValidationError(f'账号已被锁定，请{remaining_time}分钟后重试')

        if not user.check_password(password):
            # 统一错误信息，不泄漏剩余尝试次数
            raise serializers.ValidationError('用户名或密码错误')

        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'role_display', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
