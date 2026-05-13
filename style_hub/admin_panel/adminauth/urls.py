from django.urls import path
from . import views 

urlpatterns = [
    path('',views.admin_login,name='admin_login'),
    path('admin_forgottpassword/',views.admin_forgottpassword,name='admin_forgottpassword'),
    path('admin_emailverification/',views.admin_emailverification,name='admin_emailverification'),
    path('admin_resetpassword/',views.admin_resetpassword,name='admin_resetpassword'),
    path('admin_logout',views.admin_logout,name='admin_logout')

]
