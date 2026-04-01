from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from projects.models import Project
from crm.models import Supplier
from .models import MaterialNew, EquipmentNew, MaterialIO, EquipmentIO


class MaterialNewTests(TestCase):
    """物料管理测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='invuser', password='Test123456')
        self.supplier = Supplier.objects.create(name='物料供应商', status='active', contact='13800138001')
        self.client.force_authenticate(user=self.user)

    def test_create_material(self):
        """创建物料"""
        data = {
            'name': '测试物料',
            'specification': '规格型号A',
            'unit': 'pcs',
            'stock': 100,
            'alert_threshold': 10,
            'supplier': self.supplier.id
        }
        response = self.client.post('/api/v1/inventory/material_new/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试物料')

    def test_list_materials(self):
        """列出物料"""
        MaterialNew.objects.create(name='物料A', stock=50)
        MaterialNew.objects.create(name='物料B', stock=80)
        response = self.client.get('/api/v1/inventory/material_new/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 2)

    def test_update_material(self):
        """更新物料"""
        material = MaterialNew.objects.create(name='旧物料', stock=100)
        data = {'name': '新物料', 'stock': 200}
        response = self.client.patch(f'/api/v1/inventory/material_new/{material.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], '新物料')

    def test_delete_material(self):
        """删除物料"""
        material = MaterialNew.objects.create(name='待删除', stock=50)
        response = self.client.delete(f'/api/v1/inventory/material_new/{material.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class EquipmentNewTests(TestCase):
    """设备管理测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='equipuser', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_create_equipment(self):
        """创建设备"""
        data = {
            'name': '测试设备',
            'specification': '型号X',
            'model': 'MODEL-X',
            'status': 'idle',
            'location': '仓库A'
        }
        response = self.client.post('/api/v1/inventory/equipment_new/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试设备')

    def test_list_equipment(self):
        """列出设备"""
        EquipmentNew.objects.create(name='设备A', status='idle')
        EquipmentNew.objects.create(name='设备B', status='in_use')
        response = self.client.get('/api/v1/inventory/equipment_new/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_equipment_status(self):
        """更新设备状态"""
        equip = EquipmentNew.objects.create(name='设备', status='idle')
        data = {'status': 'in_use'}
        response = self.client.patch(f'/api/v1/inventory/equipment_new/{equip.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'in_use')


class MaterialIOTests(TestCase):
    """物料出入库测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='matiouser', password='Test123456')
        self.project = Project.objects.create(name='库存测试项目', status='ongoing')
        self.material = MaterialNew.objects.create(name='测试物料', stock=100, alert_threshold=10)
        self.client.force_authenticate(user=self.user)

    def test_material_in(self):
        """物料入库"""
        data = {
            'material': self.material.id,
            'type': 'in',
            'quantity': 50,
            'project': self.project.id,
            'remark': '采购入库'
        }
        response = self.client.post('/api/v1/inventory/material_io/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.material.refresh_from_db()
        self.assertEqual(float(self.material.stock), 150.0)

    def test_material_out(self):
        """物料出库"""
        data = {
            'material': self.material.id,
            'type': 'out',
            'quantity': 30,
            'project': self.project.id
        }
        response = self.client.post('/api/v1/inventory/material_io/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.material.refresh_from_db()
        self.assertEqual(float(self.material.stock), 70.0)

    def test_material_out_insufficient(self):
        """库存不足仍可出库（记录为已知问题）"""
        data = {
            'material': self.material.id,
            'type': 'out',
            'quantity': 200,  # 超过库存100
            'project': self.project.id
        }
        response = self.client.post('/api/v1/inventory/material_io/', data)
        # 当前无库存校验，允许超卖
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.material.refresh_from_db()
        self.assertEqual(float(self.material.stock), -100.0)  # 负数库存


class EquipmentIOTests(TestCase):
    """设备出入库测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='equipiouser', password='Test123456')
        self.project = Project.objects.create(name='设备项目', status='ongoing')
        self.equipment = EquipmentNew.objects.create(name='测试设备', status='idle')
        self.client.force_authenticate(user=self.user)

    def test_equipment_borrow(self):
        """设备领用"""
        data = {
            'equipment': self.equipment.id,
            'type': 'borrow',
            'quantity': 1,
            'project': self.project.id
        }
        response = self.client.post('/api/v1/inventory/equipment_io/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_equipment_return(self):
        """设备归还"""
        # 先领用
        EquipmentIO.objects.create(
            equipment=self.equipment, type='borrow', quantity=1,
            project=self.project, operator=self.user
        )
        data = {
            'equipment': self.equipment.id,
            'type': 'return',
            'quantity': 1,
            'project': self.project.id
        }
        response = self.client.post('/api/v1/inventory/equipment_io/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class InventoryBoundaryTests(TestCase):
    """库存边界测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='invboundary', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_negative_stock_initial(self):
        """初始库存为负数"""
        data = {'name': '负库存物料', 'stock': -50}
        response = self.client.post('/api/v1/inventory/material_new/', data)
        # 当前无校验
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/inventory/material_new/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
