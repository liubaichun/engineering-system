"""
GPS定位与考勤签到模块 - API视图

提供REST API的视图实现
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import base64
import io

from .models import (
    ProjectGPSSettings, Worker, WorkerGroup,
    AttendanceQRCode, AttendanceRecord
)
from .serializers import (
    LocationValidateSerializer, GPSConfigSerializer, GPSConfigUpdateSerializer,
    CheckInSerializer, CheckOutSerializer, QRCodeGenerateSerializer,
    AttendanceRecordSerializer
)


class LocationValidateView(APIView):
    """
    POST /api/v1/attendance/location/validate/
    
    校验位置是否在工地范围内
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LocationValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 40001,
                'message': '参数校验失败',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project_id = serializer.validated_data['project_id']
        latitude = float(serializer.validated_data['latitude'])
        longitude = float(serializer.validated_data['longitude'])
        
        # 获取项目GPS配置
        try:
            gps_settings = ProjectGPSSettings.objects.get(project_id=project_id)
        except ProjectGPSSettings.DoesNotExist:
            return Response({
                'code': 40003,
                'message': '该项目未配置GPS信息',
                'detail': {'project_id': project_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 校验位置
        validation_result = gps_settings.validate_location(latitude, longitude)
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'is_within_range': validation_result['is_within_range'],
                'distance_meters': validation_result['distance_meters'],
                'allowed_radius': validation_result['allowed_radius'],
                'project_name': gps_settings.project.name,
                'project_address': gps_settings.address
            }
        }, status=status.HTTP_200_OK)


class ProjectGPSConfigView(APIView):
    """
    GET /api/v1/attendance/projects/{project_id}/gps-config/
    PUT /api/v1/attendance/projects/{project_id}/gps-config/
    
    获取/设置项目GPS配置
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        """获取项目GPS配置"""
        try:
            gps_settings = ProjectGPSSettings.objects.get(project_id=project_id)
        except ProjectGPSSettings.DoesNotExist:
            return Response({
                'code': 40003,
                'message': '该项目未配置GPS信息',
                'detail': {'project_id': project_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = GPSConfigSerializer(gps_settings)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, project_id):
        """更新项目GPS配置"""
        serializer = GPSConfigUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 40001,
                'message': '参数校验失败',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取或创建GPS配置
        gps_settings, created = ProjectGPSSettings.objects.get_or_create(
            project_id=project_id,
            defaults={
                'center_latitude': serializer.validated_data['center_latitude'],
                'center_longitude': serializer.validated_data['center_longitude'],
                'radius_meters': serializer.validated_data.get('radius_meters', 500),
                'is_enabled': serializer.validated_data.get('is_enabled', True),
                'address': serializer.validated_data.get('address', '')
            }
        )
        
        if not created:
            # 更新现有配置
            for field in ['center_latitude', 'center_longitude', 'radius_meters', 'is_enabled', 'address']:
                if field in serializer.validated_data:
                    setattr(gps_settings, field, serializer.validated_data[field])
            gps_settings.save()
        
        response_serializer = GPSConfigSerializer(gps_settings)
        return Response({
            'code': 0,
            'message': 'GPS配置更新成功',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)


class CheckInView(APIView):
    """
    POST /api/v1/attendance/checkin/
    
    二维码签到（含GPS）
    """
    permission_classes = []  # Allow anonymous
    
    @transaction.atomic
    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 40001,
                'message': '参数校验失败',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        qr_id = serializer.validated_data['qr_id']
        worker_id = serializer.validated_data['worker_id']
        latitude = float(serializer.validated_data['latitude'])
        longitude = float(serializer.validated_data['longitude'])
        check_in_time = serializer.validated_data.get('check_in_time') or timezone.now()
        
        # 校验二维码
        try:
            qr_code = AttendanceQRCode.objects.select_for_update().get(qr_id=qr_id)
        except AttendanceQRCode.DoesNotExist:
            return Response({
                'code': 40004,
                'message': '二维码无效或已过期',
                'detail': {'qr_id': qr_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not qr_code.is_valid():
            return Response({
                'code': 40004,
                'message': '二维码无效或已过期',
                'detail': {'qr_id': qr_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 校验工人
        try:
            worker = Worker.objects.get(id=worker_id, is_deleted=False)
        except Worker.DoesNotExist:
            return Response({
                'code': 40006,
                'message': '工人ID不存在',
                'detail': {'worker_id': worker_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取项目GPS配置并校验位置
        try:
            gps_settings = ProjectGPSSettings.objects.get(project_id=qr_code.project_id)
            validation_result = gps_settings.validate_location(latitude, longitude)
        except ProjectGPSSettings.DoesNotExist:
            validation_result = {
                'is_within_range': True,
                'distance_meters': 0,
                'allowed_radius': 0
            }
        
        # 创建签到记录
        record = AttendanceRecord.objects.create(
            worker=worker,
            project=qr_code.project,
            group=qr_code.group,
            check_in_time=check_in_time,
            check_in_latitude=latitude,
            check_in_longitude=longitude,
            check_in_location_valid=validation_result['is_within_range'],
            check_in_distance_meters=validation_result.get('distance_meters'),
            qr_code=qr_code,
            status=AttendanceRecord.Status.NORMAL
        )
        
        # 标记二维码已使用
        qr_code.mark_used(worker)
        
        # 自动判断迟到
        normal_start_hour = 9
        if check_in_time.hour > normal_start_hour:
            record.status = AttendanceRecord.Status.LATE
            record.save(update_fields=['status'])
        
        message = '签到成功'
        if not validation_result['is_within_range']:
            message = '签到成功，但位置超出工地范围'
        
        return Response({
            'code': 0,
            'message': message,
            'data': {
                'record_id': record.id,
                'worker_name': worker.name,
                'project_name': qr_code.project.name,
                'check_in_time': record.check_in_time,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'is_valid': validation_result['is_within_range'],
                    'distance_meters': validation_result.get('distance_meters', 0),
                    'allowed_radius': validation_result.get('allowed_radius', 0)
                },
                'status': record.status,
                'status_text': record.get_status_display()
            }
        }, status=status.HTTP_201_CREATED)


class CheckOutView(APIView):
    """
    POST /api/v1/attendance/checkout/
    
    签退（含GPS）
    """
    permission_classes = []  # Allow anonymous
    
    @transaction.atomic
    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 40001,
                'message': '参数校验失败',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        record_id = serializer.validated_data['record_id']
        latitude = float(serializer.validated_data['latitude'])
        longitude = float(serializer.validated_data['longitude'])
        check_out_time = serializer.validated_data.get('check_out_time') or timezone.now()
        
        # 获取签到记录
        try:
            record = AttendanceRecord.objects.select_for_update().get(
                id=record_id,
                is_deleted=False
            )
        except AttendanceRecord.DoesNotExist:
            return Response({
                'code': 40008,
                'message': '签到记录不存在',
                'detail': {'record_id': record_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if record.check_out_time:
            return Response({
                'code': 40009,
                'message': '该记录已签退',
                'detail': {'record_id': record_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取项目GPS配置并校验位置
        try:
            gps_settings = ProjectGPSSettings.objects.get(project_id=record.project_id)
            validation_result = gps_settings.validate_location(latitude, longitude)
        except ProjectGPSSettings.DoesNotExist:
            validation_result = {
                'is_within_range': True,
                'distance_meters': 0,
                'allowed_radius': 0
            }
        
        # 更新签退信息
        record.check_out_time = check_out_time
        record.check_out_latitude = latitude
        record.check_out_longitude = longitude
        record.check_out_location_valid = validation_result['is_within_range']
        record.check_out_distance_meters = validation_result.get('distance_meters')
        
        # 自动判断早退
        normal_end_hour = 18
        if check_out_time.hour < normal_end_hour:
            if record.status == AttendanceRecord.Status.NORMAL:
                record.status = AttendanceRecord.Status.EARLY_LEAVE
        
        record.save()
        
        return Response({
            'code': 0,
            'message': '签退成功',
            'data': {
                'record_id': record.id,
                'worker_name': record.worker.name,
                'check_in_time': record.check_in_time,
                'check_out_time': record.check_out_time,
                'working_hours': record.working_hours,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'is_valid': validation_result['is_within_range'],
                    'distance_meters': validation_result.get('distance_meters', 0),
                    'allowed_radius': validation_result.get('allowed_radius', 0)
                },
                'status': record.status,
                'status_text': record.get_status_display()
            }
        }, status=status.HTTP_200_OK)


class QRCodeGenerateView(APIView):
    """
    POST /api/v1/attendance/qrcode/generate/
    
    生成签到二维码
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = QRCodeGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 40001,
                'message': '参数校验失败',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project_id = serializer.validated_data['project_id']
        group_id = serializer.validated_data.get('group_id')
        valid_hours = serializer.validated_data.get('valid_hours', 24)
        
        from projects.models import Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                'code': 40002,
                'message': '项目ID不存在',
                'detail': {'project_id': project_id}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        group = None
        if group_id:
            try:
                group = WorkerGroup.objects.get(id=group_id)
            except WorkerGroup.DoesNotExist:
                return Response({
                    'code': 40010,
                    'message': '班组ID不存在',
                    'detail': {'group_id': group_id}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        now = timezone.now()
        valid_until = now + timedelta(hours=valid_hours)
        
        # 创建二维码
        qr_code = AttendanceQRCode.objects.create(
            project=project,
            group=group,
            valid_from=now,
            valid_until=valid_until,
            created_by=request.user
        )
        
        # 生成二维码内容URL
        qr_content = f"{request.scheme}://{request.get_host()}/api/v1/attendance/checkin/?qr_id={qr_code.qr_id}"
        
        # 生成二维码图片（Base64编码）
        qr_image_base64 = self._generate_qr_code_base64(qr_content)
        
        return Response({
            'code': 0,
            'message': '二维码生成成功',
            'data': {
                'qr_id': qr_code.qr_id,
                'qr_content': qr_content,
                'project_name': project.name,
                'group_name': group.name if group else None,
                'valid_from': qr_code.valid_from,
                'valid_until': qr_code.valid_until,
                'qr_image_base64': qr_image_base64
            }
        }, status=status.HTTP_201_CREATED)
    
    def _generate_qr_code_base64(self, content):
        """生成二维码图片并返回Base64编码"""
        try:
            import qrcode
            from PIL import Image
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except ImportError:
            # 如果没有 qrcode 库，返回占位符
            return ''


class MyAttendanceRecordsView(APIView):
    """
    GET /api/v1/attendance/records/my/
    
    获取当前施工人员的考勤记录
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date_str = request.query_params.get('date')
        
        if date_str:
            try:
                from datetime import datetime
                query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'code': 40007,
                    'message': '日期格式错误，应为YYYY-MM-DD',
                    'detail': {'date': date_str}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = timezone.now().date()
        
        # 获取当前用户关联的施工人员
        try:
            worker = Worker.objects.get(is_deleted=False)
            # 如果需要关联用户，可以在这里过滤
        except Worker.DoesNotExist:
            return Response({
                'code': 40006,
                'message': '当前用户未关联施工人员'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        records = AttendanceRecord.objects.filter(
            worker=worker,
            is_deleted=False,
            check_in_time__date=query_date
        ).order_by('-check_in_time')
        
        serializer = AttendanceRecordSerializer(records, many=True)
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'date': query_date.strftime('%Y-%m-%d'),
                'records': serializer.data
            }
        }, status=status.HTTP_200_OK)


class QRCodeListView(APIView):
    """
    GET /api/v1/attendance/qrcodes/
    
    获取二维码列表（管理端）
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        project_id = request.GET.get('project_id')
        
        qrcodes = AttendanceQRCode.objects.select_related('project', 'group').all()
        if project_id:
            qrcodes = qrcodes.filter(project_id=project_id)
        
        qrcodes = qrcodes.order_by('-created_at')[:100]
        
        results = []
        for qr in qrcodes:
            results.append({
                'id': qr.id,
                'qr_id': qr.qr_id,
                'project_id': qr.project_id,
                'project_name': qr.project.name,
                'group_id': qr.group_id,
                'group_name': qr.group.name if qr.group else None,
                'valid_from': qr.valid_from.isoformat() if qr.valid_from else None,
                'valid_until': qr.valid_until.isoformat() if qr.valid_until else None,
                'is_used': qr.is_used,
                'used_by': qr.used_by.name if qr.used_by else None,
                'used_at': qr.used_at.isoformat() if qr.used_at else None,
                'created_at': qr.created_at.isoformat() if qr.created_at else None,
            })
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': results
        })


class AttendanceRecordListView(APIView):
    """
    GET /api/v1/attendance/records/
    
    获取考勤记录列表（管理端）
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        project_id = request.GET.get('project_id')
        worker_name = request.GET.get('worker_name')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        records = AttendanceRecord.objects.select_related('worker', 'project', 'group').filter(is_deleted=False)
        
        if project_id:
            records = records.filter(project_id=project_id)
        if worker_name:
            records = records.filter(worker__name__icontains=worker_name)
        if date_from:
            records = records.filter(check_in_time__gte=date_from)
        if date_to:
            records = records.filter(check_in_time__lte=date_to)
        
        records = records.order_by('-check_in_time')[:200]
        
        results = []
        for r in records:
            results.append({
                'record_id': r.id,
                'worker_id': r.worker_id,
                'worker_name': r.worker.name,
                'project_id': r.project_id,
                'project_name': r.project.name,
                'group_name': r.group.name if r.group else None,
                'check_in_time': r.check_in_time.isoformat() if r.check_in_time else None,
                'check_in_location_valid': r.check_in_location_valid,
                'check_in_distance_meters': r.check_in_distance_meters,
                'check_out_time': r.check_out_time.isoformat() if r.check_out_time else None,
                'check_out_location_valid': r.check_out_location_valid,
                'check_out_distance_meters': r.check_out_distance_meters,
                'working_hours': r.working_hours,
                'status': r.status,
                'status_text': r.get_status_display(),
            })
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': results
        })


class WorkerLookupView(APIView):
    """
    GET /api/v1/attendance/workers/lookup/?phone=xxx or /id_card=xxx

    根据手机号或身份证号查询施工人员
    允许匿名访问，但必须提供有效认证Token才能返回完整信息
    """
    permission_classes = [AllowAny]  # 改为AllowAny，内部手动认证

    def get(self, request):
        # 手动Token认证检查
        auth = request.auth
        if not auth or not request.user.is_authenticated:
            return Response({
                'code': 40101,
                'message': '未授权访问，请先登录'
            }, status=status.HTTP_401_UNAUTHORIZED)

        phone = request.GET.get('phone')
        id_card = request.GET.get('id_card')

        if not phone and not id_card:
            return Response({
                'code': 40001,
                'message': '请提供手机号或身份证号'
            }, status=status.HTTP_400_BAD_REQUEST)

        workers = Worker.objects.filter(is_deleted=False).select_related('group')
        if phone:
            workers = workers.filter(phone=phone)
        if id_card:
            workers = workers.filter(id_card_number=id_card)

        workers = workers[:1]
        if not workers:
            return Response({
                'code': 40401,
                'message': '未找到该施工人员'
            }, status=status.HTTP_404_NOT_FOUND)

        w = workers[0]
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'worker_id': w.id,
                'name': w.name,
                'phone': w.phone,
                'id_card_number': w.id_card_number,
                'work_type': w.work_type,
                'skill_level': w.skill_level,
                'group_name': w.group.name if w.group else None,
            }
        })


class WorkerListView(APIView):
    """
    GET /api/v1/attendance/workers/
    
    获取施工人员列表
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        project_id = request.GET.get('project_id')
        group_id = request.GET.get('group_id')
        
        workers = Worker.objects.filter(is_deleted=False)
        if group_id:
            workers = workers.filter(group_id=group_id)
        
        workers = workers.order_by('-created_at')[:100]
        
        results = []
        for w in workers:
            results.append({
                'worker_id': w.id,
                'name': w.name,
                'phone': w.phone,
                'id_card_number': w.id_card_number,
                'work_type': w.work_type,
                'skill_level': w.skill_level,
                'group_name': w.group.name if w.group else None,
                'status': w.status,
            })
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': results
        })


class WorkerCreateView(APIView):
    """
    POST /api/v1/attendance/workers/create/
    
    创建施工人员
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        name = request.data.get('name')
        id_card_number = request.data.get('id_card_number')
        phone = request.data.get('phone')
        work_type = request.data.get('work_type', 'general')
        skill_level = request.data.get('skill_level', 'junior')
        entry_date = request.data.get('entry_date')
        
        if not name or not id_card_number or not phone:
            return Response({
                'code': 40001,
                'message': '姓名、身份证号、手机号为必填项'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否已存在
        if Worker.objects.filter(id_card_number=id_card_number, is_deleted=False).exists():
            return Response({
                'code': 40002,
                'message': '该身份证号已存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Worker.objects.filter(phone=phone, is_deleted=False).exists():
            return Response({
                'code': 40003,
                'message': '该手机号已存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from django.utils import timezone
        from datetime import datetime
        
        entry = None
        if entry_date:
            try:
                entry = datetime.strptime(entry_date, '%Y-%m-%d').date()
            except:
                pass
        
        worker = Worker.objects.create(
            name=name,
            id_card_number=id_card_number,
            phone=phone,
            work_type=work_type,
            skill_level=skill_level,
            entry_date=entry,
            status='active'
        )
        
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': {
                'worker_id': worker.id,
                'name': worker.name,
                'phone': worker.phone,
                'id_card_number': worker.id_card_number,
                'work_type': worker.work_type,
                'skill_level': worker.skill_level,
                'group_name': None,
                'status': worker.status,
                'entry_date': str(worker.entry_date) if worker.entry_date else None,
            }
        })


class WorkerLocationView(APIView):
    """
    GET /api/v1/attendance/workers/locations/
    
    获取施工人员当前位置列表（基于今日最新签到记录）
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        返回所有有有效GPS坐标的施工人员当前位置
        用于在地图上展示工人分布
        """
        project_id = request.GET.get('project_id')
        date_str = request.GET.get('date')
        
        # 默认查询今日
        if date_str:
            try:
                from datetime import datetime
                query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'code': 40007,
                    'message': '日期格式错误，应为YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = timezone.now().date()
        
        # 获取当日的考勤记录（只取有GPS坐标的）
        records = AttendanceRecord.objects.select_related(
            'worker', 'project', 'group'
        ).filter(
            is_deleted=False,
            check_in_time__date=query_date
        ).exclude(
            check_in_latitude__isnull=True,
            check_in_longitude__isnull=True
        )
        
        if project_id:
            records = records.filter(project_id=project_id)
        
        # 按工人分组，只取每个工人最新的一条记录
        worker_latest = {}
        for record in records.order_by('-check_in_time'):
            worker_id = record.worker_id
            if worker_id not in worker_latest:
                worker_latest[worker_id] = record
        
        results = []
        for worker_id, record in worker_latest.items():
            # 判断当前状态：是否已签退
            is_checked_out = record.check_out_time is not None
            
            results.append({
                'worker_id': record.worker_id,
                'worker_name': record.worker.name,
                'worker_phone': record.worker.phone,
                'work_type': record.worker.work_type,
                'skill_level': record.worker.skill_level,
                'group_name': record.group.name if record.group else None,
                'project_id': record.project_id,
                'project_name': record.project.name,
                'latitude': float(record.check_in_latitude),
                'longitude': float(record.check_in_longitude),
                'is_valid': record.check_in_location_valid,
                'distance_meters': record.check_in_distance_meters,
                'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
                'is_checked_out': is_checked_out,
                'status': '已签退' if is_checked_out else '工作中',
                'working_hours': record.working_hours,
            })
        
        # 获取项目列表（用于前端筛选）
        projects = []
        if project_id:
            project_list = [record.project for record in records.distinct('project')]
        else:
            from projects.models import Project
            project_list = Project.objects.filter(
                id__in=records.values_list('project_id', flat=True).distinct()
            )
        
        for p in project_list:
            projects.append({
                'id': p.id,
                'name': p.name
            })
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'date': query_date.strftime('%Y-%m-%d'),
                'total_workers': len(results),
                'checked_in_count': sum(1 for r in results if not r['is_checked_out']),
                'checked_out_count': sum(1 for r in results if r['is_checked_out']),
                'workers': results,
                'projects': projects
            }
        })


class WorkerDeleteView(APIView):
    """
    DELETE /api/v1/attendance/workers/<id>/
    
    软删除施工人员
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, worker_id):
        try:
            worker = Worker.objects.get(id=worker_id, is_deleted=False)
        except Worker.DoesNotExist:
            return Response({
                'code': 40401,
                'message': '施工人员不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 软删除
        worker.is_deleted = True
        worker.save(update_fields=['is_deleted'])
        
        return Response({
            'code': 0,
            'message': '删除成功'
        })


class AttendanceRecordDeleteView(APIView):
    """
    DELETE /api/v1/attendance/records/<id>/
    
    软删除考勤记录
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, record_id):
        try:
            record = AttendanceRecord.objects.get(id=record_id, is_deleted=False)
        except AttendanceRecord.DoesNotExist:
            return Response({
                'code': 40401,
                'message': '考勤记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 软删除
        record.is_deleted = True
        record.save(update_fields=['is_deleted'])
        
        return Response({
            'code': 0,
            'message': '删除成功'
        })
