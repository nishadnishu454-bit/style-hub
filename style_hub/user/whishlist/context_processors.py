from .models import Wishlist

def wishlist_count(request):
    
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(
            user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True
        ).count()
        return {'wishlist_count': count}
    return {'wishlist_count': 0}
