from django.urls import path
from . import views

urlpatterns = [
    path('',views.address_page,name='address_page'),
    path('add_address/',views.add_address_page,name='add_address'),
    path('edit_address/<int:id>/',views.edit_address_page,name='edit_address'),
    path('delete_address/<int:id>/',views.delete_address,name='delete_address'),
    path('set-default-address/<int:id>/',views.set_default_address,name='set_default_address'),
    
]
