from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_page, name='wallet_page'),
    path('add-money/', views.add_money, name='add_money'),
    path('verify-wallet-payment/', views.verify_wallet_payment, name='verify_wallet_payment'),
]