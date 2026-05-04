from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_page, name='profile'),
    path('editprofile/', views.editprofile_page, name='editprofile'),
    path('verify-changed-email/', views.verify_changed_email, name='verify_changed_email'),
    path('changepassword/', views.change_password, name='changepassword'),
    
   
]   