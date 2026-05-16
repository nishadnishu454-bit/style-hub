from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
     path('',include('user.core.urls')),
    path('authentication/', include('user.authentication.urls')),
    path('profile/', include('user.profile.urls')),
    path('accounts/', include('allauth.urls')),
    path('address/',include('user.addresses.urls')),
    path('admin_login/',include('admin_panel.adminauth.urls')),
    path('admin_dashboard/',include('admin_panel.admindashboard.urls')),
    path('user_management/',include('admin_panel.usermanagement.urls')),
    path('category_management/',include('admin_panel.categorymanagement.urls')),
    path('product_management/',include('admin_panel.productmanagement.urls')),
    path('products/',include('user.products.urls')),
    path('category/',include('user.category.urls')),
    path('cart/',include('user.cart.urls')),
    path('whislist/',include('user.whishlist.urls')),
    path('order_management/',include('admin_panel.ordermanagement.urls')),
    path('checkout/',include('user.checkout.urls')),
    path('orders/',include('user.orders.urls')),
    path('coupon_management/',include('admin_panel.couponmanagement.urls')),
    path('wallet/',include('user.wallet.urls')),
   


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)