from django.urls import path
from . import views

urlpatterns = [
    path('',views.orders_listing,name='orders_listing'),
    path('order_details/<int:id>/',views.order_details,name='order_details'),
    path('update_status/<int:id>/',views.update_status,name='update_status'),
    path('return_requests/', views.return_requests, name='return_requests'),
    path('approve_return/', views.approve_return, name='approve_return'),
    path('reject_return/', views.reject_return, name='reject_return'),
]
