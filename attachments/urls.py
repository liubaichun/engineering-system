from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.AttachmentCategoryViewSet, basename='attachment-category')
router.register(r'folders', views.ProjectFileFolderViewSet, basename='project-folder')
router.register(r'project-attachments', views.ProjectAttachmentViewSet, basename='project-attachment')
router.register(r'task-attachments', views.TaskAttachmentViewSet, basename='task-attachment')
router.register(r'batch-download', views.BatchDownloadViewSet, basename='batch-download')
router.register(r'file-ops', views.AttachmentRenameViewSet, basename='file-ops')
router.register(r'storage-stats', views.StorageStatsViewSet, basename='storage-stats')
router.register(r'', views.AttachmentViewSet, basename='attachment')

urlpatterns = [
    path('', include(router.urls)),
]
