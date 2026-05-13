from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
import uuid

from user.addresses.models import Address
from user.cart.models import Cart
from user.orders.models import Order, OrderItem


@login_required(login_url='login')
def checkout_page(request):

    cart_items = Cart.objects.filter(user=request.user).select_related(
        'variant',
        'variant__product',
        'variant__product__category'
    )

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart_page')

    # Check for out-of-stock items before allowing checkout
    for item in cart_items:
        if item.variant.variant_stock < item.quantity:
            messages.error(request, f"{item.variant.product.product_name} is out of stock or insufficient.")
            return redirect('cart_page')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()

    subtotal = Decimal('0.00')

    for item in cart_items:
        item.item_total = item.variant.variant_price * item.quantity
        subtotal += item.item_total

    discount_amount = Decimal('0.00')
    delivery_charge = Decimal('0.00')
    tax_amount = Decimal('0.00')

    total_amount = subtotal - discount_amount + delivery_charge + tax_amount

    if request.method == 'POST':

        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('checkout')

        if not payment_method:
            messages.error(request, 'Please select a payment method')
            return redirect('checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)

        try:
            with transaction.atomic():
                # Re-verify stock inside transaction
                for item in cart_items:
                    # Need to refresh variant from db to get latest stock
                    variant = item.variant
                    variant.refresh_from_db()
                    if variant.variant_stock < item.quantity:
                        messages.error(
                            request,
                            f'{variant.product.product_name} has only {variant.variant_stock} stock left'
                        )
                        return redirect('checkout')

                order = Order.objects.create(
                    user=request.user,
                    address=address,
                    order_number=f"SH-{uuid.uuid4().hex[:10].upper()}",
                    payment_method=payment_method,
                    payment_status='Pending',
                    order_status='Pending',
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    delivery_charge=delivery_charge,
                    total_amount=total_amount,
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        variant=item.variant,
                        product_name=item.variant.product.product_name,
                        price=item.variant.variant_price,
                        quantity=item.quantity,
                        total_price=item.variant.variant_price * item.quantity,
                        item_status='Pending',
                    )

                    # Reduce stock
                    item.variant.variant_stock -= item.quantity
                    item.variant.save()

                cart_items.delete()

                request.session['order_id'] = order.id

                messages.success(request, 'Order placed successfully')
                return redirect('order_success')

        except Exception as e:
            messages.error(request, f'Something went wrong: {e}')
            return redirect('checkout')

    context = {
        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'delivery_charge': delivery_charge,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'delivery_date': '3-5 Business Days', # Placeholder
    }

    return render(request, 'checkout.html', context)


