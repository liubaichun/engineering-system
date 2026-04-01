"""
GPS定位与考勤签到模块 - URL路由配置

注册在 /api/v1/attendance/ 路径下
"""

from django.urls import path
from .views import (
    LocationValidateView,
    ProjectGPSConfigView,
    CheckInView,
    CheckOutView,
    QRCodeGenerateView,
    MyAttendanceRecordsView,
    QRCodeListView,
    AttendanceRecordListView,
    WorkerLookupView,
    WorkerListView,
    WorkerCreateView,
    WorkerLocationView
)

app_name = 'gps_attendance'

urlpatterns = [
    # GPS位置校验
    path('location/validate/', LocationValidateView.as_view(), name='location-validate'),
    
    # 项目GPS配置
    path('projects/<int:project_id>/gps-config/', ProjectGPSConfigView.as_view(), name='project-gps-config'),
    
    # 签到/签退
    path('checkin/', CheckInView.as_view(), name='checkin'),
    path('checkout/', CheckOutView.as_view(), name='checkout'),
    
    # 二维码管理
    path('qrcode/generate/', QRCodeGenerateView.as_view(), name='qrcode-generate'),
    path('qrcodes/', QRCodeListView.as_view(), name='qrcodes-list'),
    
    # 考勤记录查询
    path('records/my/', MyAttendanceRecordsView.as_view(), name='my-records'),
    path('records/', AttendanceRecordListView.as_view(), name='records-list'),
    
    # 施工人员管理
    path('workers/lookup/', WorkerLookupView.as_view(), name='worker-lookup'),
    path('workers/', WorkerListView.as_view(), name='workers-list'),
    path('workers/create/', WorkerCreateView.as_view(), name='worker-create'),
    path('workers/locations/', WorkerLocationView.as_view(), name='worker-locations'),
]
