from django.urls import path
from . import views

urlpatterns = [
    path('',views.user_orders_listing,name='user_orders_listing'),
    path('orders_view/',views.orders_view,name='orders_view'),
    path('order_success/',views.order_success,name='order_success'),
    path('invoice/',views.invoice,name='invoice'),
    path('order_cancel_success/',views.order_cancel_success,name='order_cancel_success'),
    path('review_writing/',views.review_writing,name='review_writing'),
    path('return_order/',views.return_order,name='return_order')
]
