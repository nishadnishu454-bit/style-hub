from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.offer_listing, name='offer_listing'),
    path('offers/add/', views.add_offer, name='add_offer'),
    path('offers/edit/<int:id>/', views.edit_offer, name='edit_offer'),
    path('offers/delete/<int:id>/', views.delete_offer, name='delete_offer'),
    path('offers/toggle/<int:id>/', views.toggle_offer_status, name='toggle_offer_status'),
]

