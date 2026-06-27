from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_page, name='profile'),
    path('verify-changed-email/', views.verify_changed_email, name='verify_changed_email'),
    path('resend-email-change-otp/',views.resend_email_change_otp,name='resend_email_change_otp'),
    path('changepassword/', views.change_password, name='changepassword'),
    
   
]   