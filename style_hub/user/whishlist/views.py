from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from admin_panel.productmanagement.models import ProductVariant
from user.cart.models import Cart
from .models import Wishlist


@login_required(login_url='login')
def wishlist_page(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        variant__is_deleted=False,
        variant__is_active=True,
        variant__product__is_deleted=False,
        variant__product__is_active=True,
        variant__product__category__is_deleted=False,
        variant__product__category__is_active=True
    ).select_related(
        'variant',
        'variant__product',
        'variant__product__category'
    ).prefetch_related(
        'variant__images',
        'variant__product__reviews'
    ).order_by('-id')

    for item in wishlist_items:
        reviews = item.variant.product.reviews.all()
        count = len(reviews)

        if count > 0:
            item.avg_rating = round(sum(r.rating for r in reviews) / count , 1)
            item.review_count =count
        else:
            item.avg_rating =None
            item.review_count = 0



    cart_count = Cart.objects.filter(user=request.user).count()

    context = {
        'wishlist_items': wishlist_items,
        'wishlist_count': len(list(wishlist_items)),
        'cart_count': cart_count,
    }

    return render(request, 'wishlist.html', context)


@login_required(login_url='login')
def add_to_wishlist(request, id):
    variant = get_object_or_404(
        ProductVariant,
        id=id,
        is_deleted=False,
        is_active=True,
        product__is_deleted=False,
        product__is_active=True,
        product__category__is_deleted=False,
        product__category__is_active=True
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        variant=variant
    ).first()

    if wishlist_item:
        wishlist_item.delete()
        action = 'removed'
        msg = 'Removed from wishlist'
    else:
        Wishlist.objects.create(
            user=request.user,
            variant=variant
        )
        action = 'added'
        msg = 'Added to wishlist'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'action': action,
            'message': msg,
            'wishlist_count': Wishlist.objects.filter(user=request.user).count()
        })

    if action == 'added':
        messages.success(request, msg)
    else:
        messages.warning(request, msg)


    return redirect('product_detail', id=variant.product.id)

@login_required(login_url='login')
def remove_wishlist_item(request, id):
    wishlist_item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )
    wishlist_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'message': 'Item removed from wishlist',
            'wishlist_count': Wishlist.objects.filter(user=request.user).count()
        })

    messages.success(request, 'Item removed from wishlist')
    return redirect('wishlist_page')