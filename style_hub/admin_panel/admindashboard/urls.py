from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('sales-report/', views.sales_report_page, name='sales_report'),
    path('sales-report/pdf/', views.download_sales_report_pdf, name='download_sales_report_pdf'),
    path('sales-report/excel/', views.download_sales_report_excel, name='download_sales_report_excel'),
    path('referrals/', views.admin_referrals, name='admin_referrals'),
    
]
