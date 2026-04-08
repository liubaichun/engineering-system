from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import FileResponse, HttpResponse
from django.http.response import HttpResponseBase
import os, hashlib, uuid
from io import BytesIO
import zipfile
from .models import (
    Attachment, ProjectAttachment, TaskAttachment,
    AttachmentCategory, ProjectFileFolder,
    AttachmentVersion, AttachmentDownloadLog
)
from .serializers import (
    AttachmentSerializer, ProjectAttachmentSerializer, TaskAttachmentSerializer,
    AttachmentCategorySerializer, ProjectFileFolderSerializer,
    AttachmentVersionSerializer, AttachmentDownloadLogSerializer,
    AttachmentListSerializer
)

ALLOWED_FILE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv',
    '.zip', '.rar', '.7z',
    '.json', '.xml',
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class AttachmentCategoryViewSet(viewsets.ModelViewSet):
    queryset = AttachmentCategory.objects.all()
    serializer_class = AttachmentCategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=['get'])
    def tree(self, request):
        categories = AttachmentCategory.objects.filter(parent__isnull=True).order_by('order')
        result = []
        for cat in categories:
            children = AttachmentCategory.objects.filter(parent=cat).order_by('order')
            node = {
                'id': cat.id, 'name': cat.name, 'code': cat.code, 'order': cat.order,
                'children': [{'id': c.id, 'name': c.name, 'code': c.code, 'order': c.order} for c in children]
            }
            result.append(node)
        return Response(result)


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AttachmentListSerializer
        return AttachmentSerializer

    def get_queryset(self):
        queryset = Attachment.objects.all()
        project_id = self.request.query_params.get('project_id')
        category_code = self.request.query_params.get('category')
        file_type = self.request.query_params.get('file_type')
        keyword = self.request.query_params.get('q')
        if project_id:
            queryset = queryset.filter(project_attachments__project_id=project_id)
        if category_code:
            queryset = queryset.filter(category__code=category_code)
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(sub_category__icontains=keyword))
        return queryset.distinct()

    def _validate_file(self, file):
        if file.size > MAX_FILE_SIZE:
            return False, f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024*1024)}MB）"
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_FILE_EXTENSIONS:
            return False, f"不支持的文件类型：{ext}"
        return True, ""

    def _compute_md5(self, file_obj):
        h = hashlib.md5()
        for chunk in file_obj.chunks():
            h.update(chunk)
        file_obj.seek(0)
        return h.hexdigest()

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        valid, msg = self._validate_file(file)
        if not valid:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        md5_hash = self._compute_md5(file)
        response = super().create(request, *args, **kwargs)
        att_id = response.data.get('id')
        if att_id:
            att = Attachment.objects.get(id=att_id)
            att.md5 = md5_hash
            att.file_size = file.size
            att.save(update_fields=['md5', 'file_size'])
            # 自动生成缩略图（图片）
            if not att.thumbnail:
                from .utils import create_thumbnail_for_attachment
                thumb = create_thumbnail_for_attachment(att)
                if thumb:
                    Attachment.objects.filter(pk=att.pk).update(thumbnail=thumb)
        return response

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        att = self.get_object()
        vs = AttachmentVersion.objects.filter(attachment=att).order_by('-version')
        return Response(AttachmentVersionSerializer(vs, many=True).data)

    @action(detail=True, methods=['get'])
    def download_logs(self, request, pk=None):
        att = self.get_object()
        logs = AttachmentDownloadLog.objects.filter(attachment=att).order_by('-downloaded_at')[:50]
        return Response(AttachmentDownloadLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        att = self.get_object()
        self._log_action(att, request, 'download')
        if not att.file:
            return Response({'detail': 'File not found'}, status=404)
        path = att.file.path
        if not os.path.exists(path):
            return Response({'detail': 'File not found on server'}, status=404)
        response = FileResponse(open(path, 'rb'), as_attachment=True, filename=att.name)
        return response

    @action(detail=True, methods=['get'])
    def view_file(self, request, pk=None):
        att = self.get_object()
        self._log_action(att, request, 'view')
        if not att.file:
            return Response({'detail': 'File not found'}, status=404)
        path = att.file.path
        if not os.path.exists(path):
            return Response({'detail': 'File not found on server'}, status=404)
        ext = os.path.splitext(att.name)[1].lower()
        ctype_map = {
            '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
        }
        return FileResponse(open(path, 'rb'), content_type=ctype_map.get(ext, 'application/octet-stream'))

    def _log_action(self, attachment, request, action_type):
        AttachmentDownloadLog.objects.create(
            attachment=attachment,
            user=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            action=action_type
        )


class ProjectAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectAttachment.objects.all()
    serializer_class = ProjectAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = ProjectAttachment.objects.all()
        pid = self.request.query_params.get('project_id')
        cat = self.request.query_params.get('category')
        if pid:
            q = q.filter(project_id=pid)
        if cat:
            q = q.filter(attachment__category__code=cat)
        return q.select_related('attachment', 'project')


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAttachment.objects.all()
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]


class ProjectFileFolderViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectFileFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = ProjectFileFolder.objects.all()
        pid = self.request.query_params.get('project_id')
        parent = self.request.query_params.get('parent')
        cat = self.request.query_params.get('category')
        if pid:
            q = q.filter(project_id=pid)
        if parent is not None:
            q = q.filter(parent_id=parent) if parent not in ('', 'null') else q.filter(parent__isnull=True)
        if cat:
            q = q.filter(category__code=cat)
        return q.select_related('category', 'created_by', 'project')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AttachmentRenameViewSet(viewsets.ViewSet):
    """文件重命名/移动"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def rename(self, request):
        """单文件重命名: {id, name}"""
        att_id = request.data.get('id')
        new_name = request.data.get('name', '').strip()
        if not att_id or not new_name:
            return Response({'detail': 'id和name必填'}, status=400)
        try:
            att = Attachment.objects.get(id=att_id)
        except Attachment.DoesNotExist:
            return Response({'detail': '文件不存在'}, status=404)
        ext = os.path.splitext(att.name)[1]
        if not new_name.endswith(ext):
            new_name += ext
        att.name = new_name
        att.save(update_fields=['name'])
        return Response({'id': att.id, 'name': att.name})

    @action(detail=False, methods=['post'])
    def batch_rename(self, request):
        """批量重命名: [{id, name}, ...]"""
        items = request.data.get('items', [])
        if not items or not isinstance(items, list):
            return Response({'detail': 'items列表必填'}, status=400)
        if len(items) > 50:
            return Response({'detail': '最多单次50个文件'}, status=400)
        results = []
        for item in items:
            att_id = item.get('id')
            new_name = item.get('name', '').strip()
            if not att_id or not new_name:
                continue
            try:
                att = Attachment.objects.get(id=att_id)
                ext = os.path.splitext(att.name)[1]
                if not new_name.endswith(ext):
                    new_name += ext
                att.name = new_name
                att.save(update_fields=['name'])
                results.append({'id': att.id, 'name': att.name})
            except Attachment.DoesNotExist:
                continue
        return Response({'updated': results})

    @action(detail=False, methods=['post'])
    def move(self, request):
        """移动文件到文件夹: {attachment_ids: [], folder_id: int|null}"""
        att_ids = request.data.get('attachment_ids', [])
        folder_id = request.data.get('folder_id')
        if not att_ids:
            return Response({'detail': 'attachment_ids必填'}, status=400)
        if len(att_ids) > 50:
            return Response({'detail': '最多单次50个文件'}, status=400)

        if folder_id:
            try:
                folder = ProjectFileFolder.objects.get(id=folder_id)
            except ProjectFileFolder.DoesNotExist:
                return Response({'detail': '目标文件夹不存在'}, status=404)
            # 将文件关联到项目+文件夹
            from .models import ProjectAttachment
            updated = 0
            for att_id in att_ids:
                try:
                    att = Attachment.objects.get(id=att_id)
                    pa, _ = ProjectAttachment.objects.get_or_create(
                        project=folder.project, attachment=att
                    )
                    # 更新attachment的category
                    att.category = folder.category
                    att.save(update_fields=['category'])
                    updated += 1
                except Attachment.DoesNotExist:
                    continue
            return Response({'moved': updated, 'folder': folder.name})
        else:
            # 从项目中移除
            from .models import ProjectAttachment
            removed = ProjectAttachment.objects.filter(attachment_id__in=att_ids).delete()[0]
            return Response({'removed_from_project': removed})


class StorageStatsViewSet(viewsets.ViewSet):
    """存储空间统计"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """按项目统计存储空间"""
        from projects.models import Project
        from django.db.models import Count, Sum as OSSum
        # 一次性查询：按项目分组统计
        stats = (
            Project.objects.annotate(
                file_count=Count('attachments__id'),
            ).values('id', 'name', 'file_count')
        )
        result = []
        for s in stats:
            project_id = s['id']
            pa_ids = list(ProjectAttachment.objects.filter(project_id=project_id).values_list('attachment_id', flat=True))
            total = 0
            if pa_ids:
                total = Attachment.objects.filter(id__in=pa_ids).aggregate(t=OSSum('file_size'))['t'] or 0
            result.append({
                'project_id': project_id,
                'project_name': s['name'],
                'file_count': s['file_count'],
                'total_size': total,
                'total_size_mb': round(total / 1024 / 1024, 2),
            })
        result.sort(key=lambda x: x['total_size'], reverse=True)
        return Response(result)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类统计"""
        stats = []
        for cat in AttachmentCategory.objects.all():
            total_size = Attachment.objects.filter(category=cat).aggregate(
                total=models.Sum('file_size')
            )['total'] or 0
            stats.append({
                'category_id': cat.id,
                'category_name': cat.name,
                'file_count': Attachment.objects.filter(category=cat).count(),
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
            })
        stats.sort(key=lambda x: x['total_size'], reverse=True)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """全局存储汇总"""
        total_size = Attachment.objects.aggregate(total=models.Sum('file_size'))['total'] or 0
        total_count = Attachment.objects.count()
        return Response({
            'total_files': total_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'total_size_gb': round(total_size / 1024 / 1024 / 1024, 2),
        })


class BatchDownloadViewSet(viewsets.ViewSet):
    """批量打包下载"""
    permission_classes = [IsAuthenticated]

    def create(self, request):
        attachment_ids = request.data.get('attachment_ids', [])
        if not attachment_ids:
            return Response({'detail': 'attachment_ids required'}, status=400)
        if len(attachment_ids) > 50:
            return Response({'detail': '最多单次50个文件'}, status=400)

        attachments = Attachment.objects.filter(id__in=attachment_ids).select_related('uploader')
        if not attachments.exists():
            return Response({'detail': 'No valid attachments found'}, status=404)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for att in attachments:
                if att.file and att.file.name:
                    fp = att.file.path
                    if os.path.exists(fp):
                        zf.write(fp, att.name)
        zip_buffer.seek(0)

        ts = timezone.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="attachments_{ts}.zip"'
        return response
