from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from admin_panel.productmanagement.models import ProductVariant
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
    )

    context = {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_items.count()
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
        product__is_active=True
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        variant=variant
    )

    return redirect('wishlist_page')


@login_required(login_url='login')
def remove_wishlist_item(request, id):
    wishlist_item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )

    wishlist_item.delete()

    return redirect('wishlist_page')