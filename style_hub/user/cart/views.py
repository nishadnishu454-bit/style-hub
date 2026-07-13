from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart
from user.whishlist.models import Wishlist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from admin_panel.productmanagement.models import Product
from admin_panel.variantmanagement.models import ProductVariant
from django.http import JsonResponse
import json
from admin_panel.couponmanagement.models import Coupon

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
    ).select_related(
        'variant',
        'variant__product',
        'variant__product__category'
    ).prefetch_related(
        'variant__images'
    )

    sub_total = 0

    for item in cart_items:
        item.item_total = item.variant.offer_price * item.quantity
        sub_total += item.item_total

    # Calculate offer discount
    offer_discount = sum(
        (item.variant.variant_price - item.variant.offer_price) * item.quantity 
        for item in cart_items
    )
    original_subtotal = sub_total + offer_discount

    discount = 0

    if sub_total == 0:
        delivery_charge = 0
    elif sub_total >= 500:
        delivery_charge = 0
    else:
        delivery_charge = 50

    total_amount = sub_total - discount + delivery_charge

    context = {
        'cart_items': cart_items,
        'subtotal': sub_total,
        'sub_total': sub_total,
        'original_subtotal': original_subtotal,
        'offer_discount': offer_discount,
        'discount': discount,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
        'cart_count': cart_items.count(),
        'has_out_of_stock': any(item.variant.variant_stock < item.quantity for item in cart_items)
    }

    return render(request, 'cartlisting.html', context)


@login_required(login_url='login')
def add_cart(request, id):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    )

    referer = request.META.get('HTTP_REFERER')
    default_redirect = lambda: redirect('product_detail', id=product.id)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))
        except Exception:
            variant_id = None
            quantity = 1
    else:
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))

    if not variant_id:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Please select a size'},status=400)
        messages.error(request, 'Please select a size')
        return redirect(referer) if referer else default_redirect()

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        product=product,
        is_active=True,
        is_deleted=False
    )

    if variant.variant_stock <= 0:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'This product is out of stock'},status=400)
        messages.error(request, 'This product is out of stock')
        return redirect(referer) if referer else default_redirect()

    if quantity > variant.variant_stock:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Selected quantity is more than available stock'},status=400)
        messages.error(request, 'Selected quantity is more than available stock')
        return redirect(referer) if referer else default_redirect()

    if quantity > 5:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Maximum 5 quantity allowed'},status=400)
        messages.error(request, 'Maximum 5 quantity allowed')
        return redirect(referer) if referer else default_redirect()

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        variant=variant,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > variant.variant_stock:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Not enough stock available'},status=400)
            messages.error(request, 'Not enough stock available')
            return redirect(referer) if referer else default_redirect()

        if new_quantity > 5:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Maximum 5 quantity allowed'},status=400)
            messages.error(request, 'Maximum 5 quantity allowed')
            return redirect(referer) if referer else default_redirect()

        cart_item.quantity = new_quantity
        cart_item.save()

    Wishlist.objects.filter(
        user=request.user,
        variant=variant
    ).delete()

    if is_ajax:
        cart_count = Cart.objects.filter(
            user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True
        ).count()
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': cart_count
        },status=200)

    messages.success(request, 'Product added to cart')
    return redirect(referer) if referer else redirect('product_detail', id=id)


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
        messages.warning(request, 'Minimum quanity allowed is 1')
    return redirect('cart_page')




@login_required(login_url='login')
def update_cart_quantity_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_id = data.get('cart_id')
            action = data.get('action')
            
            cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
            variant = cart_item.variant
            
            deleted = False
            message = ""
            status = True
            
            if action == 'increase':
                if cart_item.quantity < variant.variant_stock:
                    if cart_item.quantity < 5:
                        cart_item.quantity += 1
                        cart_item.save()
                    else:
                        status = False
                        message = "Maximum 5 quantity allowed"
                else:
                    status = False
                    message = "Stock limit reached"
                    
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    status = False
                    message = "Minimum quantity allowed is 1"
                    
            
            # Recalculate totals
            cart_items = Cart.objects.filter(
                user=request.user,
                variant__is_deleted=False,
                variant__is_active=True,
                variant__product__is_deleted=False,
                variant__product__is_active=True,
                variant__product__category__is_deleted=False,
                variant__product__category__is_active=True
                )
            
            sub_total = sum(item.variant.offer_price * item.quantity for item in cart_items)

            # Revalidate session coupon
            coupon_id = request.session.get('coupon_id')
            coupon_removed = False
            if coupon_id:
                coupon = Coupon.objects.filter(id=coupon_id, is_active=True, is_deleted=False).first()
                if coupon:
                    if sub_total < coupon.min_purchase:
                        request.session.pop('coupon_id', None)
                        request.session.pop('discount_amount', None)
                        coupon_removed = True
                        message = f"Coupon '{coupon.code}' removed: minimum purchase of ₹{coupon.min_purchase} not met."
                else:
                    request.session.pop('coupon_id', None)
                    request.session.pop('discount_amount', None)
                    coupon_removed = True
                    message = "Applied coupon is no longer valid."

            offer_discount = sum((item.variant.variant_price - item.variant.offer_price) * item.quantity for item in cart_items)
            original_subtotal = sub_total + offer_discount
            
            discount = 0
            if sub_total == 0:
                delivery_charge = 0
            elif sub_total >= 500:
                delivery_charge = 0
            else:
                delivery_charge = 50
                
            total_amount = sub_total - discount + delivery_charge
            item_total = cart_item.variant.offer_price * cart_item.quantity if not deleted else 0
            
            return JsonResponse({
                'status': status,
                'message': message,
                'coupon_removed': coupon_removed,
                'quantity': 0 if deleted else cart_item.quantity,
                'item_total': 0 if deleted else cart_item.variant.offer_price * cart_item.quantity if not deleted else 0,
                'sub_total': sub_total,
                'subtotal': sub_total,
                'original_subtotal': original_subtotal,
                'offer_discount': offer_discount,
                'discount': discount,
                'delivery_charge': "FREE" if delivery_charge == 0 and sub_total > 0 else f"₹{delivery_charge}",
                'total_amount': total_amount,
                'cart_count': cart_items.count(),
                'deleted': deleted,
                'has_out_of_stock': any(item.variant.variant_stock < item.quantity for item in cart_items)
            },status=200)
            
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)},status=500)
            
    return JsonResponse({'status': False, 'message': 'Invalid request'},status=400)


@login_required(login_url='login')
def remove_cart_item(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)
    cart_item.delete()

    messages.success(request, 'Item removed from cart')
    return redirect('cart_page')