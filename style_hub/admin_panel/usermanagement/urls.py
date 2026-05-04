from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detial'),
    path('users/<int:user_id>/block/', views.block_user, name='block_user'),
    path('users/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),
]