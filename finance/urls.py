from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'income', views.IncomeViewSet, basename='income')
router.register(r'expense', views.ExpenseViewSet, basename='expense')
router.register(r'invoices', views.InvoiceNewViewSet, basename='invoice')
router.register(r'records', views.FinancialRecordViewSet, basename='financial-record')

urlpatterns = [
    path('', include(router.urls)),
]
