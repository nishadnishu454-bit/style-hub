from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart
from user.whishlist.models import Wishlist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from admin_panel.productmanagement.models import ProductVariant, Product


@login_required(login_url='login')
def cart_page(request):
    cart_items = Cart.objects.filter(
    user=request.user,
    variant__is_deleted=False,
    variant__is_active=True,
    variant__product__is_deleted=False,
    variant__product__is_active=True,
    variant__product__category__is_deleted=False,
    variant__product__category__is_active=True
)

    sub_total = 0

    for item in cart_items:
        item.item_total = item.variant.variant_price * item.quantity
        sub_total += item.item_total

    discount = 0
    delivery_charge = 0 if sub_total >= 500 else 50
    total_amount = sub_total - discount + delivery_charge

    context = {
        'cart_items': cart_items,
        'subtotal': sub_total,
        'sub_total': sub_total,
        'discount': discount,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
        'cart_count': cart_items.count()
    }

    return render(request, 'cartlisting.html', context)


@login_required(login_url='login')
def add_cart(request, id):
    product = get_object_or_404(Product, id=id, is_deleted=False, is_active=True)

    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    if not variant_id:
        messages.error(request, 'Please select a size')
        return redirect('product_detail', id=product.id)

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        product=product,
        is_active=True,
        is_deleted=False
    )

    if quantity > variant.variant_stock:
        messages.error(request, 'Selected quantity is more than available stock')
        return redirect('product_detail', id=product.id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        variant=variant,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > variant.variant_stock:
            messages.error(request, 'Not enough stock available')
            return redirect('product_detail', id=product.id)

        cart_item.quantity = new_quantity
        cart_item.save()

    messages.success(request, 'Product added to cart')
    return redirect('cart_page')
   

@login_required(login_url='login')
def increase_cart_quantity(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)

    if cart_item.quantity < cart_item.variant.variant_stock and cart_item.quantity < 5:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.error(request, 'Stock limit reached')

    return redirect('cart_page')


@login_required(login_url='login')
def decrease_cart_quantity(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart_page')


@login_required(login_url='login')
def remove_cart_item(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)
    cart_item.delete()

    messages.success(request, 'Item removed from cart')
    return redirect('cart_page')

