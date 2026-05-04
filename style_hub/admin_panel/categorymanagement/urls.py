from django.urls import path
from . import views

urlpatterns = [
    path('', views.category_listing, name='category_listing'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<int:id>/', views.edit_category, name='edit_category'),
    path('delete_category/<int:id>/', views.delete_category, name='delete_category'),
    path('activate_category/<int:id>/', views.activate_category, name='activate_category'),
    path('deactivate_category/<int:id>/', views.deactivate_category, name='deactivate_category'),
]