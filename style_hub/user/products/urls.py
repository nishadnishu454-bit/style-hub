from django.urls import path
from . import views

urlpatterns = [
    path('',views.product_page,name='product_page'),
    path('product_detail/<int:id>/',views.product_detail,name='product_detail'),
    path('buy_now/',views.buy_now,name='buy_now')
]
