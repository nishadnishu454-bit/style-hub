from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.variant_management, name='variant_management'),
    path('add_variant/<int:product_id>/', views.add_variant, name='add_variant'),
    path('edit_variant/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('delete_variant/<int:variant_id>/', views.delete_variant, name='delete_variant'),
]
