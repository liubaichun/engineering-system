from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.ExportProjectsView.as_view(), name='export_projects'),
    path('tasks/', views.ExportTasksView.as_view(), name='export_tasks'),
    path('materials/', views.ExportMaterialsView.as_view(), name='export_materials'),
    path('equipment/', views.ExportEquipmentView.as_view(), name='export_equipment'),
    path('import/projects/', views.ImportProjectsView.as_view(), name='import_projects'),
]
