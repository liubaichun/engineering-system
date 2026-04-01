from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from projects.models import Project
from apps.gps_attendance.models import Worker, AttendanceQRCode, AttendanceRecord


class AttendanceQRCodeTests(TestCase):
    """签到二维码测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='attuser', password='Test123456')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name='考勤测试项目', status='preparing')

    def test_generate_qrcode(self):
        """生成签到二维码"""
        data = {'project_id': self.project.id, 'valid_hours': 24}
        response = self.client.post('/api/v1/attendance/qrcode/generate/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('qr_id', response.json())
        self.assertIn('qr_content', response.json())

    def test_qrcode_validity_check(self):
        """二维码有效性检查"""
        now = timezone.now()
        qr = AttendanceQRCode.objects.create(
            project=self.project,
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
            created_by=self.user
        )
        self.assertTrue(qr.is_valid())

    def test_qrcode_expired(self):
        """过期二维码"""
        now = timezone.now()
        qr = AttendanceQRCode.objects.create(
            project=self.project,
            valid_from=now - timedelta(hours=3),
            valid_until=now - timedelta(hours=1),
            created_by=self.user
        )
        self.assertFalse(qr.is_valid())


class CheckInTests(TestCase):
    """签到测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='attuser2', password='Test123456')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name='签到测试项目', status='preparing')
        self.worker = Worker.objects.create(
            name='测试工人',
            id_card_number='110101199001011234',
            phone='13800138000',
            work_type='general',
            status='active'
        )
        self.now = timezone.now()
        self.qr = AttendanceQRCode.objects.create(
            project=self.project,
            valid_from=self.now - timedelta(hours=1),
            valid_until=self.now + timedelta(hours=1),
            created_by=self.user
        )

    def test_checkin_success(self):
        """正常签到"""
        data = {
            'qr_id': self.qr.qr_id,
            'worker_id': self.worker.id,
            'latitude': 39.9042,
            'longitude': 116.4074
        }
        response = self.client.post('/api/v1/attendance/checkin/', data)
        # 签到成功（无GPS配置时is_within_range=True）
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['code'], 0)

    def test_checkin_invalid_qr(self):
        """无效二维码"""
        data = {
            'qr_id': 'nonexistent_qr',
            'worker_id': self.worker.id,
            'latitude': 39.9042,
            'longitude': 116.4074
        }
        response = self.client.post('/api/v1/attendance/checkin/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 40004)

    def test_checkin_invalid_worker(self):
        """无效工人"""
        data = {
            'qr_id': self.qr.qr_id,
            'worker_id': 99999,
            'latitude': 39.9042,
            'longitude': 116.4074
        }
        response = self.client.post('/api/v1/attendance/checkin/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_latitude_out_of_range(self):
        """纬度越界"""
        data = {
            'qr_id': self.qr.qr_id,
            'worker_id': self.worker.id,
            'latitude': 999.0,  # 非法纬度
            'longitude': 116.4074
        }
        response = self.client.post('/api/v1/attendance/checkin/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_success(self):
        """正常签退"""
        # 先签到
        checkin_data = {
            'qr_id': self.qr.qr_id,
            'worker_id': self.worker.id,
            'latitude': 39.9042,
            'longitude': 116.4074
        }
        checkin_resp = self.client.post('/api/v1/attendance/checkin/', checkin_data)
        record_id = checkin_resp.json()['data']['record_id']

        # 签退
        checkout_data = {
            'record_id': record_id,
            'latitude': 39.9042,
            'longitude': 116.4074
        }
        response = self.client.post('/api/v1/attendance/checkout/', checkout_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('working_hours', response.json())


class AttendanceRecordTests(TestCase):
    """考勤记录查询测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='attuser3', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_list_attendance_records(self):
        """获取考勤记录列表"""
        response = self.client.get('/api/v1/attendance/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())


class WorkerLocationTests(TestCase):
    """施工人员定位测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='locuser', password='Test123456')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name='定位测试项目', status='preparing')
        self.worker = Worker.objects.create(
            name='定位测试工人',
            id_card_number='110101199001019999',
            phone='13900139000',
            work_type='electrician',
            status='active'
        )

    def test_get_worker_locations(self):
        """获取工人位置列表"""
        response = self.client.get('/api/v1/attendance/workers/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertIn('workers', data)
        self.assertIn('projects', data)
        self.assertIn('total_workers', data)
        self.assertIn('checked_in_count', data)
        self.assertIn('checked_out_count', data)

    def test_get_worker_locations_with_project_filter(self):
        """按项目筛选工人位置"""
        response = self.client.get(f'/api/v1/attendance/workers/locations/?project_id={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['code'], 0)

    def test_get_worker_locations_with_date_filter(self):
        """按日期筛选工人位置"""
        today = timezone.now().strftime('%Y-%m-%d')
        response = self.client.get(f'/api/v1/attendance/workers/locations/?date={today}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['date'], today)

    def test_get_worker_locations_invalid_date(self):
        """无效日期格式"""
        response = self.client.get('/api/v1/attendance/workers/locations/?date=invalid-date')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 40007)
