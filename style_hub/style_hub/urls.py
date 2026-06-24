from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.core.urls')),
    path('authentication/', include('user.authentication.urls')),
    path('login/', RedirectView.as_view(url='/authentication/', permanent=False)),
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
    path('offer_management/',include('admin_panel.offermanagement.urls')),
    path('variant_management/',include('admin_panel.variantmanagement.urls')),
    path('review_management/',include('admin_panel.reviewmanagement.urls'))
   


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



handler404 = 'style_hub.views.custom_404'
handler500 = 'style_hub.views.custom_500'
handler403 = 'style_hub.views.custom_403'
handler400 = 'style_hub.views.custom_400'