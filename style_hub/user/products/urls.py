from django.urls import path
from . import views

urlpatterns = [
    path('',views.prodcut_page,name='product_page')
]
