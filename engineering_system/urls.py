"""
URL configuration for engineering_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from knox import views as knox_views
from knox.auth import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.views import LoginView as KnoxLoginViewOverride  # 覆写Knox的LoginView以修复permission_classes


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_view(request):
    """全局搜索 API"""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})
    
    results = []
    user = request.user
    
    # 搜索项目 - 非admin用户只搜关联项目
    from projects.models import Project
    if user.role == 'admin':
        projects = Project.objects.filter(
            Q(name__icontains=q) | Q(client__name__icontains=q) | Q(description__icontains=q)
        )[:5]
    else:
        projects = Project.objects.filter(
            Q(manager=user) &
            (Q(name__icontains=q) | Q(client__name__icontains=q) | Q(description__icontains=q))
        )[:5]
    for p in projects:
        results.append({
            'type': 'project', 'id': p.id, 'name': p.name,
            'detail': f'{p.get_status_display()} | {p.client or ""}'
        })
    
    # 搜索客户
    from crm.models import Customer
    customers = Customer.objects.filter(
        Q(name__icontains=q) | Q(contact__icontains=q)
    )[:5]
    for c in customers:
        results.append({
            'type': 'customer', 'id': c.id, 'name': c.name,
            'detail': f'{c.get_status_display() if hasattr(c, "get_status_display") else ""} | {c.contact or ""}'
        })
    
    # 搜索任务
    from tasks.models import Task
    tasks = Task.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q)
    )[:5]
    for t in tasks:
        results.append({
            'type': 'task', 'id': t.id, 'name': t.name,
            'detail': f'{t.get_status_display() if hasattr(t, "get_status_display") else t.status}'
        })
    
    # 搜索供应商
    from crm.models import Supplier
    suppliers = Supplier.objects.filter(
        Q(name__icontains=q) | Q(contact__icontains=q)
    )[:5]
    for s in suppliers:
        results.append({
            'type': 'supplier', 'id': s.id, 'name': s.name,
            'detail': s.contact or ''
        })
    
    return JsonResponse({'results': results})

def login_page(request):
    return render(request, 'login.html')

def index_page(request):
    return render(request, 'login.html')

def projects_page(request):
    return render(request, 'projects.html')

def dashboard_page(request):
    return render(request, 'dashboard.html')

def users_page(request):
    return render(request, 'users.html')

def tasks_page(request):
    return render(request, 'tasks.html')

def customers_page(request):
    return render(request, 'customers.html')

def suppliers_page(request):
    return render(request, 'suppliers.html')

def finance_page(request):
    return render(request, 'finance.html')

def materials_page(request):
    return render(request, 'materials.html')

def equipment_page(request):
    return render(request, 'equipment.html')

def system_page(request):
    return render(request, 'system.html')

def stats_page(request):
    return render(request, 'stats.html')

def gantt_page(request):
    return render(request, 'gantt.html')

def approval_page(request):
    return render(request, 'approval.html')

def reminders_page(request):
    return render(request, 'reminders.html')

def materials_equipment_page(request):
    return render(request, 'materials_equipment.html')


def exports_page(request):
    return render(request, 'exports.html')

def signin_page(request):
    return render(request, 'signin.html')

def signin_admin_page(request):
    return render(request, 'signin_admin.html')

def workers_page(request):
    return render(request, 'workers.html')

def worker_location_page(request):
    return render(request, 'worker_location.html')



# Prometheus Metrics Endpoint
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def metrics(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    path('api/v1/auth/login/', KnoxLoginViewOverride.as_view(), name='knox_login'),
    path('api/v1/auth/', include('knox.urls')),
    path('api/v1/health/', lambda _: JsonResponse({'status': 'ok', 'service': 'engineering_system'}), name='health'),
    path('admin/', admin.site.urls),
    path('', index_page, name='index'),
    path('login/', login_page, name='login'),
    path('dashboard/', dashboard_page, name='dashboard'),
    path('users/', users_page, name='users'),
    path('projects/', projects_page, name='projects'),
    path('tasks/', tasks_page, name='tasks'),
    path('customers/', customers_page, name='customers'),
    path('suppliers/', suppliers_page, name='suppliers'),
    path('finance/', finance_page, name='finance'),
    path('materials/', materials_page, name='materials'),
    path('equipment/', equipment_page, name='equipment'),
    path('system/', system_page, name='system'),
    path('stats/', stats_page, name='stats'),
    path('gantt/', gantt_page, name='gantt'),
    path('approval/', approval_page, name='approval'),
    path('approvals.html', lambda request: render(request, 'approvals.html'), name='approvals_page'),
    path('reminders/', reminders_page, name='reminders'),
    path('notifications/', lambda request: render(request, 'notifications.html'), name='notifications'),
    path('materials_equipment/', materials_equipment_page, name='materials_equipment'),
    path('exports/', exports_page, name='exports'),
    path('signin/', signin_page, name='signin_page'),
    path('signin/admin/', signin_admin_page, name='signin_admin_page'),
    path('workers/', workers_page, name='workers_page'),
    path('files/', lambda request: render(request, 'files.html'), name='files_page'),
    path('worker_location/', worker_location_page, name='worker_location_page'),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/projects/', include('projects.urls')),
    path('api/v1/tasks/', include('tasks.urls')),
    path('api/v1/crm/', include('crm.urls')),
    path('api/v1/finance/', include('finance.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/attachments/', include('attachments.urls')),
    path('api/v1/export/', include('exports.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/approvals/', include('approvals.urls')),
    path('api/v1/operation_logs/', include('operation_logs.urls')),
    path('api/v1/workers/', include('apps.workers.urls')),
    path('api/v1/attendance/', include('apps.gps_attendance.urls')),
    path('api/v1/search/', search_view, name='search'),
    path('metrics/', metrics, name='metrics'),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
