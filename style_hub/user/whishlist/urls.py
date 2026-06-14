from django.urls import path
from . import views


urlpatterns = [
    path('', views.wishlist_page, name='wishlist_page'),
    path('add/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<int:id>/', views.remove_wishlist_item, name='remove_wishlist_item'),
]

