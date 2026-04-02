from rest_framework import serializers
from .models import Income, Expense, InvoiceNew, FinancialRecord, Invoice
from datetime import date as date_class


class NullableDateField(serializers.DateField):
    """支持空字符串和null的DateField，空值时返回当天日期"""
    def to_internal_value(self, data):
        if data == '' or data is None:
            return date_class.today()
        return super().to_internal_value(data)
    
    def validate_empty_values(self, data):
        # 拦截 null 和空字符串，在 to_internal_value 之前转换为今天日期
        if data is None or data == '':
            return (False, date_class.today())  # 继续正常流程
        return super().validate_empty_values(data)


class IncomeSerializer(serializers.ModelSerializer):
    """收入序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, allow_null=True)
    # 前端使用 client 字段，映射到模型的 customer 字段
    client = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    # remark 是前端字段，静默忽略
    remark = serializers.CharField(required=False, allow_blank=True, write_only=True)
    # date 允许 null/空值，由 NullableDateField 处理默认值
    date = NullableDateField(required=False, allow_null=True)
    
    class Meta:
        model = Income
        fields = [
            'id', 'amount', 'date', 'project', 'project_name',
            'customer', 'customer_name', 'client',
            'description', 'attachment', 'remark', 'operator', 'operator_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('金额不能为负数')
        return value

    def create(self, validated_data):
        # 处理前端 client 字段映射到模型的 customer 字段（仅当 customer 未显式提供时）
        client_id = validated_data.pop('client', None)
        validated_data.pop('remark', None)  # 移除前端字段，不存入模型
        if 'customer' not in validated_data and client_id is not None:
            validated_data['customer_id'] = client_id
        return super().create(validated_data)
    
    def validate_date(self, value):
        # NullableDateField 返回 None 时，转换为今天
        if value is None:
            return date_class.today()
        return value
    
    def validate(self, attrs):
        # 处理完全缺失的 date 字段：使用默认值
        if 'date' not in attrs:
            attrs['date'] = date_class.today()
        return attrs
    
    def update(self, instance, validated_data):
        client_id = validated_data.pop('client', None)
        validated_data.pop('remark', None)
        if 'customer' not in validated_data and client_id is not None:
            validated_data['customer_id'] = client_id
        return super().update(instance, validated_data)


class ExpenseSerializer(serializers.ModelSerializer):
    """支出序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, allow_null=True)
    # date 允许 null/空值，由 NullableDateField 处理默认值
    date = NullableDateField(required=False, allow_null=True)
    # remark 是前端字段，静默忽略
    remark = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'amount', 'expense_type', 'date', 'project', 'project_name',
            'supplier', 'supplier_name', 'description', 'attachment', 'remark', 'operator', 'operator_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('金额不能为负数')
        # 仅费用报销禁止零金额，预付款/押金允许
        expense_type = self.initial_data.get('expense_type', 'expense')
        if expense_type == 'expense' and value == 0:
            raise serializers.ValidationError('金额不能为零')
        return value

    def create(self, validated_data):
        validated_data.pop('remark', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('remark', None)
        return super().update(instance, validated_data)
    
    def validate(self, attrs):
        # 处理完全缺失的 date 字段：使用默认值
        if 'date' not in attrs:
            attrs['date'] = date_class.today()
        return attrs


class InvoiceNewSerializer(serializers.ModelSerializer):
    """发票序列化器（新）"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    
    class Meta:
        model = InvoiceNew
        fields = [
            'id', 'invoice_no', 'type', 'type_display', 'amount',
            'project', 'project_name', 'status', 'status_display',
            'issue_date', 'due_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FinancialRecordSerializer(serializers.ModelSerializer):
    """财务记录序列化器（兼容）"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    
    class Meta:
        model = FinancialRecord
        fields = [
            'id', 'project', 'project_name', 'type', 'type_display',
            'amount', 'category', 'description', 'status', 'status_display',
            'is_locked', 'operator', 'operator_name', 'record_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """发票序列化器（兼容）"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'record', 'invoice_number', 'status', 'status_display',
            'invoice_date', 'amount', 'verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at']
