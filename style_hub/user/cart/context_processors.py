from .models import Cart


def cart_count(request):
    
    count = 0

    if request.user.is_authenticated:
        count = Cart.objects.filter(
            user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True
        ).count()

    return {
        'cart_count': count
    } 