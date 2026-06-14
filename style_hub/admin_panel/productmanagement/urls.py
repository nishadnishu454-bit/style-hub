from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_listing, name='product_listing'),
    path('view/<int:id>/', views.view_product, name='view_product'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:id>/', views.edit_product, name='edit_product'),
    path('activate_product/<int:id>/', views.activate_product, name='activate_product'),
    path('deactivate_product/<int:id>/', views.deactivate_product, name='deactivate_product'),
    path('delete/<int:id>/', views.delete_product, name='delete_product'),
    
]