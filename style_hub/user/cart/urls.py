from django.urls import path
from . import views
urlpatterns = [
    path('',views.cart_page,name='cart_page'),
    path('add_cart/<int:id>/',views.add_cart,name = 'add_cart'),
    path('increase-cart-quantity/<int:id>/',views.increase_cart_quantity,name='increase_cart_quantity'),
    path('decrease-cart-quantity/<int:id>/',views.decrease_cart_quantity,name='decrease_cart_quantity'),
    path('remove-cart-item/<int:id>/',views.remove_cart_item,name='remove_cart_item'),
    path('update-quantity/', views.update_cart_quantity_ajax, name='update_cart_quantity_ajax'),
]
