from django.core.management.base import BaseCommand
from attachments.models import AttachmentCategory


class Command(BaseCommand):
    def handle(self, *args, **options):
        categories = [
            {'name': '图纸', 'code': 'drawing', 'order': 1},
            {'name': '合同', 'code': 'contract', 'order': 2},
            {'name': '方案', 'code': 'plan', 'order': 3},
            {'name': '照片', 'code': 'photo', 'order': 4},
            {'name': '竣工资料', 'code': 'asbuilt', 'order': 5},
            {'name': '设备清单', 'code': 'equipment', 'order': 6},
            {'name': '测试报告', 'code': 'test_report', 'order': 7},
        ]

        for cat in categories:
            obj, created = AttachmentCategory.objects.get_or_create(
                code=cat['code'],
                defaults={'name': cat['name'], 'order': cat['order']}
            )
            status = '创建' if created else '已存在'
            self.stdout.write(f"[{status}] {obj.name} (code={obj.code})")
