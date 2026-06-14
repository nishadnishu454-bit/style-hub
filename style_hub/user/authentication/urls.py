from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('email_verification/', views.email_verification, name='email_verification'),
    path('forgott_password/', views.forgott_password, name='auth_forgott_password'),
    path('auth_verify_changed_password/',views.verify_changed_password,name='auth_verify_changed_password'),
    path('resend-signup-otp/', views.resend_signup_otp, name='resend_signup_otp'),
    path('resend-password-reset-otp/',views.resend_password_reset_otp,name='resend_password_reset_otp'),
    path('reset_password/', views.reset_password, name='auth_reset_password'),
    path('logout/',views.logout_user, name='logout_user'),

]