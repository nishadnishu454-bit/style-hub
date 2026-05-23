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
    path('variants/', views.variant_management, name='variant_management'),
    path('add_variant/<int:product_id>/', views.add_variant, name='add_variant'),
    path('edit_variant/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('delete_variant/<int:variant_id>/', views.delete_variant, name='delete_variant'),
    
    # Offer module URLs
    path('offers/', views.offer_listing, name='offer_listing'),
    path('offers/add/', views.add_offer, name='add_offer'),
    path('offers/edit/<int:id>/', views.edit_offer, name='edit_offer'),
    path('offers/delete/<int:id>/', views.delete_offer, name='delete_offer'),
    path('offers/toggle/<int:id>/', views.toggle_offer_status, name='toggle_offer_status'),
]