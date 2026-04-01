from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import uuid
import json
from .models import Project, SignInRecord, SignInQRCode
from .serializers import ProjectSerializer


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # 签到API允许匿名访问
def signin_api(request):
    """
    扫码签到API
    GET: 获取签到状态或验证二维码
    POST: 提交签到记录
    """
    if request.method == 'GET':
        # 验证二维码是否有效
        code = request.GET.get('code', '')
        if not code:
            return Response({'success': False, 'message': '缺少二维码编号'}, status=400)
        
        try:
            qr = SignInQRCode.objects.get(code=code, is_active=True)
            now = timezone.now()
            if now < qr.valid_from:
                return Response({'success': False, 'message': '二维码尚未生效', 'valid_from': qr.valid_from.isoformat()}, status=400)
            if now > qr.valid_until:
                return Response({'success': False, 'message': '二维码已过期', 'valid_until': qr.valid_until.isoformat()}, status=400)
            
            return Response({
                'success': True,
                'message': '二维码有效',
                'data': {
                    'id': qr.id,
                    'name': qr.name,
                    'project_id': qr.project.id,
                    'project_name': qr.project.name,
                    'location_name': qr.location_name,
                    'valid_from': qr.valid_from.isoformat(),
                    'valid_until': qr.valid_until.isoformat(),
                }
            })
        except SignInQRCode.DoesNotExist:
            return Response({'success': False, 'message': '二维码无效或已停用'}, status=404)
    
    elif request.method == 'POST':
        # 提交签到
        data = request.data
        code = data.get('code', '')
        person_name = data.get('person_name', '')
        person_phone = data.get('person_phone', '')
        person_company = data.get('person_company', '')
        sign_type = data.get('sign_type', 'checkin')
        remark = data.get('remark', '')
        latitude = data.get('latitude', '')
        longitude = data.get('longitude', '')
        location = data.get('location', '')
        
        if not code:
            return Response({'success': False, 'message': '缺少二维码编号'}, status=400)
        if not person_name:
            return Response({'success': False, 'message': '请填写签到人姓名'}, status=400)
        
        try:
            qr = SignInQRCode.objects.get(code=code, is_active=True)
            now = timezone.now()
            if now < qr.valid_from or now > qr.valid_until:
                return Response({'success': False, 'message': '二维码不在有效期内'}, status=400)
            
            record = SignInRecord.objects.create(
                project=qr.project,
                qrcode_id=code,
                person_name=person_name,
                person_phone=person_phone,
                person_company=person_company,
                sign_type=sign_type,
                remark=remark,
                latitude=latitude,
                longitude=longitude,
                location=location or qr.location_name,
            )
            
            return Response({
                'success': True,
                'message': f"{'签到' if sign_type == 'checkin' else '签退'}成功",
                'data': {
                    'id': record.id,
                    'person_name': record.person_name,
                    'sign_type': record.sign_type,
                    'sign_time': record.sign_time.isoformat(),
                    'project_name': qr.project.name,
                    'location': record.location,
                }
            })
        except SignInQRCode.DoesNotExist:
            return Response({'success': False, 'message': '二维码无效或已停用'}, status=404)
        except Exception as e:
            return Response({'success': False, 'message': f'签到失败: {str(e)}'}, status=500)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def signin_qrcode_management(request):
    """
    签到二维码管理API（需要登录）
    GET: 获取二维码列表
    POST: 创建新二维码
    """
    if request.method == 'GET':
        project_id = request.query_params.get('project_id')
        qrcodes = SignInQRCode.objects.all()
        if project_id:
            qrcodes = qrcodes.filter(project_id=project_id)
        
        data = [{
            'id': qr.id,
            'name': qr.name,
            'code': qr.code,
            'project_id': qr.project.id,
            'project_name': qr.project.name,
            'location_name': qr.location_name,
            'valid_from': qr.valid_from.isoformat(),
            'valid_until': qr.valid_until.isoformat(),
            'is_active': qr.is_active,
            'created_at': qr.created_at.isoformat(),
        } for qr in qrcodes]
        
        return Response({'success': True, 'data': data})
    
    elif request.method == 'POST':
        data = request.data
        project_id = data.get('project_id')
        name = data.get('name', '')
        location_name = data.get('location_name', '')
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        latitude = data.get('latitude', '')
        longitude = data.get('longitude', '')
        
        if not project_id:
            return Response({'success': False, 'message': '请选择项目'}, status=400)
        if not name:
            return Response({'success': False, 'message': '请填写二维码名称'}, status=400)
        if not valid_from or not valid_until:
            return Response({'success': False, 'message': '请设置有效时间'}, status=400)
        
        try:
            project = Project.objects.get(id=project_id)
            valid_from_dt = parse_datetime(valid_from) if isinstance(valid_from, str) else valid_from
            valid_until_dt = parse_datetime(valid_until) if isinstance(valid_until, str) else valid_until
            
            qr = SignInQRCode.objects.create(
                project=project,
                name=name,
                code=str(uuid.uuid4())[:16].upper(),
                location_name=location_name,
                valid_from=valid_from_dt,
                valid_until=valid_until_dt,
                latitude=latitude,
                longitude=longitude,
                created_by=request.user,
            )
            
            return Response({
                'success': True,
                'message': '二维码创建成功',
                'data': {
                    'id': qr.id,
                    'code': qr.code,
                    'name': qr.name,
                }
            })
        except Project.DoesNotExist:
            return Response({'success': False, 'message': '项目不存在'}, status=404)
        except Exception as e:
            return Response({'success': False, 'message': f'创建失败: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def signin_records(request):
    """
    签到记录查询API（需要登录）
    """
    project_id = request.query_params.get('project_id')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    person_name = request.query_params.get('person_name')
    
    records = SignInRecord.objects.all().select_related('project')
    
    if project_id:
        records = records.filter(project_id=project_id)
    if date_from:
        records = records.filter(sign_time__gte=date_from)
    if date_to:
        records = records.filter(sign_time__lte=date_to)
    if person_name:
        records = records.filter(person_name__icontains=person_name)
    
    data = [{
        'id': r.id,
        'person_name': r.person_name,
        'person_phone': r.person_phone,
        'person_company': r.person_company,
        'sign_type': r.sign_type,
        'sign_time': r.sign_time.isoformat(),
        'project_name': r.project.name if r.project else '',
        'location': r.location,
        'remark': r.remark,
    } for r in records[:100]]
    
    return Response({'success': True, 'data': data})
