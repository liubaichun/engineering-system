from rest_framework import serializers
from .models import MaterialNew, MaterialIO, EquipmentNew, EquipmentIO


class MaterialNewSerializer(serializers.ModelSerializer):
    """物料序列化器（新）"""
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)

    class Meta:
        model = MaterialNew
        fields = [
            'id', 'name', 'specification', 'unit', 'unit_display',
            'stock', 'alert_threshold', 'unit_price',
            'supplier', 'supplier_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('库存数量不能为负数')
        return value


class MaterialIOSerializer(serializers.ModelSerializer):
    """物料出入库序列化器"""
    material_name = serializers.CharField(source='material.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)

    class Meta:
        model = MaterialIO
        fields = [
            'id', 'material', 'material_name', 'type', 'type_display',
            'quantity', 'project', 'project_name', 'operator', 'operator_name',
            'remark', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        io_type = attrs.get('type')
        quantity = attrs.get('quantity')
        material = attrs.get('material')

        if io_type == 'out' and material and quantity is not None:
            if material.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'库存不足，当前库存{material.stock}，请求出库{quantity}'
                })
        return attrs


class EquipmentNewSerializer(serializers.ModelSerializer):
    """设备序列化器（新）"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EquipmentNew
        fields = [
            'id', 'name', 'specification', 'model', 'status', 'status_display',
            'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EquipmentIOSerializer(serializers.ModelSerializer):
    """设备出入库序列化器"""
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    
    class Meta:
        model = EquipmentIO
        fields = [
            'id', 'equipment', 'equipment_name', 'type', 'type_display',
            'quantity', 'project', 'project_name', 'operator', 'operator_name',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
