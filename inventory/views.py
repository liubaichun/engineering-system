from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import MaterialNew, MaterialIO, EquipmentNew, EquipmentIO
from .serializers import (
    MaterialNewSerializer, MaterialIOSerializer,
    EquipmentNewSerializer, EquipmentIOSerializer
)


class MaterialViewSet(viewsets.ModelViewSet):
    """物料视图集"""
    queryset = MaterialNew.objects.all()
    serializer_class = MaterialNewSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class MaterialIOViewSet(viewsets.ModelViewSet):
    """物料出入库视图集"""
    queryset = MaterialIO.objects.all()
    serializer_class = MaterialIOSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class EquipmentViewSet(viewsets.ModelViewSet):
    """设备视图集"""
    queryset = EquipmentNew.objects.all()
    serializer_class = EquipmentNewSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class EquipmentIOViewSet(viewsets.ModelViewSet):
    """设备出入库视图集"""
    queryset = EquipmentIO.objects.all()
    serializer_class = EquipmentIOSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]
