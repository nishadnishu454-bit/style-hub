from django.urls import path
from . import views 

urlpatterns = [
    path('', views.checkout_page, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('verify-razorpay-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('payment-failure/', views.payment_failure_page, name='payment_failure'),
    path('retry-payment/', views.retry_razorpay_payment, name='retry_payment'),
    path('create-failed-order/', views.create_failed_order, name='create_failed_order'),
]
