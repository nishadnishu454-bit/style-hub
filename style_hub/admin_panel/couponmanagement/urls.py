from django.urls import path
from . import views

urlpatterns = [
    path('', views.coupon_listing, name='coupon_listing'),
    path('add/', views.add_coupon, name='add_coupon'),
    path('edit/<int:id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/<int:id>/', views.delete_coupon, name='delete_coupon'),
    path('toggle/<int:id>/', views.toggle_coupon_status, name='toggle_coupon_status'),
]
