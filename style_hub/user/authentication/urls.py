from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('email_verfication/', views.email_verfication, name='email_verfication'),
    path('forgott_password/', views.forgott_password, name='auth_forgott_password'),
    path('reset_otp/',views.resend_otp,name='resend_otp'),
    path('auth_verify_changed_password/',views.verify_changed_password,name='auth_verify_changed_password'),
    path('reset_password/', views.reset_password, name='auth_reset_password'),
    path('logout/',views.logout_user, name='logout_user'),

]