from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from decimal import Decimal
import uuid
import razorpay
from user.addresses.models import Address
from user.cart.models import Cart
from user.orders.models import Order, OrderItem
from admin_panel.couponmanagement.models import Coupon



client = razorpay.Client(auth=( settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))
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

    applied_coupon = None
    discount_amount = Decimal('0.00')

    coupon_id = request.session.get('coupon_id')

    if coupon_id:
        applied_coupon = Coupon.objects.filter(
            id=coupon_id,
            is_active=True,
            is_deleted=False
        ).first()

        if applied_coupon:
            discount_amount = Decimal(str(request.session.get('discount_amount', 0)))
        else:
            request.session.pop('coupon_id', None)
            request.session.pop('discount_amount', None)

    if subtotal >= 500:
        delivery_charge = Decimal('0.00')
    else:
        delivery_charge = Decimal('50.00')

    tax_amount = Decimal('0.00')

    total_amount = subtotal - discount_amount + delivery_charge + tax_amount

    if total_amount < 0:
        total_amount = Decimal('0.00')

    today = timezone.now().date()

    available_coupons = Coupon.objects.filter(
        is_active=True,
        is_deleted=False,
        start_date__lte=today,
        end_date__gte=today
    )

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

                for item in cart_items:
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
 


                if payment_method == 'RAZORPAY':

                    razorpay_order = client.order.create({
                        "amount": int(total_amount * 100),
                        "currency": "INR",
                        "payment_capture": "1"
                    })

                    order.razorpay_order_id = razorpay_order['id']
                    order.save()

                    request.session['pending_order_id'] = order.id

                    return JsonResponse({
                        'success': True,
                        'razorpay': True,
                        'order_id': razorpay_order['id'],
                        'amount': int(total_amount * 100),
                        'key': settings.RAZORPAY_KEY_ID,
                        'name': 'STYLE-HUB',
                        'description': 'Order Payment',
                    })

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

                    item.variant.variant_stock -= item.quantity
                    item.variant.save()

                cart_items.delete()

                request.session.pop('coupon_id', None)
                request.session.pop('discount_amount', None)

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
        'applied_coupon': applied_coupon,
        'discount_amount': discount_amount,
        'delivery_charge': delivery_charge,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'delivery_date': '3-5 Business Days',
        'available_coupons': available_coupons,
    }

    return render(request, 'checkout.html', context)


@login_required(login_url='login')
def verify_razorpay_payment(request):

    if request.method == 'POST':

        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        pending_order_id = request.session.get('pending_order_id')

        if not pending_order_id:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            })

        order = get_object_or_404(
            Order,
            id=pending_order_id,
            user=request.user
        )

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            order.payment_status = 'Completed'
            order.order_status = 'Confirmed'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()

            cart_items = Cart.objects.filter(user=request.user).select_related(
                'variant',
                'variant__product'
            )

            for item in cart_items:

                variant = item.variant
                variant.refresh_from_db()

                if variant.variant_stock < item.quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'{variant.product.product_name} stock not available'
                    })

                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    product_name=variant.product.product_name,
                    price=variant.variant_price,
                    quantity=item.quantity,
                    total_price=variant.variant_price * item.quantity,
                    item_status='Confirmed',
                )

                variant.variant_stock -= item.quantity
                variant.save()

            cart_items.delete()

            request.session.pop('coupon_id', None)
            request.session.pop('discount_amount', None)
            request.session.pop('pending_order_id', None)

            request.session['order_id'] = order.id

            return JsonResponse({
                'success': True,
                'redirect_url': '/orders/order_success/'
            })

        except Exception as e:

            order.payment_status = 'Failed'
            order.save()

            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })


@login_required(login_url='login')
def apply_coupon(request):

    if request.method == 'POST':

        coupon_code = request.POST.get('coupon_code', '').strip()

        if not coupon_code:
            messages.error(request, 'Please enter coupon code')
            return redirect('checkout')

        if request.session.get('coupon_id'):
            messages.error(request, 'Coupon already applied')
            return redirect('checkout')

        coupon = Coupon.objects.filter(
            code__iexact=coupon_code,
            is_active=True,
            is_deleted=False
        ).first()

        if not coupon:
            messages.error(request, 'Invalid coupon code')
            return redirect('checkout')

        today = timezone.now().date()

        if coupon.start_date > today:
            messages.error(request, 'Coupon not started yet')
            return redirect('checkout')

        if coupon.end_date < today:
            messages.error(request, 'Coupon expired')
            return redirect('checkout')

        cart_items = Cart.objects.filter(user=request.user)

        subtotal = Decimal('0.00')

        for item in cart_items:
            subtotal += item.variant.variant_price * item.quantity

        if subtotal <= 0:
            messages.error(request, 'Your cart is empty')
            return redirect('cart_page')

        if subtotal < coupon.min_purchase:
            messages.error(request, f'Minimum purchase amount is ₹{coupon.min_purchase}')
            return redirect('checkout')

        if coupon.discount_type == 'PERCENTAGE':
            discount_amount = subtotal * coupon.discount_value / Decimal('100')
        else:
            discount_amount = coupon.discount_value

        if coupon.max_discount and discount_amount > coupon.max_discount:
            discount_amount = coupon.max_discount

        if discount_amount > subtotal:
            discount_amount = subtotal

        request.session['coupon_id'] = coupon.id
        request.session['discount_amount'] = str(discount_amount)

        messages.success(request, 'Coupon applied successfully')
        return redirect('checkout')

    return redirect('checkout')


@login_required(login_url='login')
def remove_coupon(request):

    request.session.pop('coupon_id', None)
    request.session.pop('discount_amount', None)

    messages.success(request, 'Coupon removed successfully')
    return redirect('checkout')