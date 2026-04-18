from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'income', views.IncomeViewSet, basename='income')
router.register(r'expense', views.ExpenseViewSet, basename='expense')
router.register(r'invoices', views.InvoiceNewViewSet, basename='invoice')
router.register(r'records', views.FinancialRecordViewSet, basename='financial-record')
router.register(r'salary', views.SalaryViewSet, basename='salary')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'monthly-report', views.MonthlyReportViewSet, basename='monthly-report')

urlpatterns = [
    path('', include(router.urls)),
]
