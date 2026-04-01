from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'contracts', views.ContractViewSet, basename='contract')

urlpatterns = [
    path('', include(router.urls)),
]
