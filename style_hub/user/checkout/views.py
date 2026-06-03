from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
import uuid
import razorpay
from user.addresses.models import Address
from user.cart.models import Cart
from user.orders.models import Order, OrderItem
from admin_panel.couponmanagement.models import Coupon
from user.wallet.models import Wallet, WalletTransaction
from user.wallet.utils import debit_wallet
from user.authentication.models import Referral
from user.wallet.utils import credit_wallet
from user.orders.models import Order
import traceback
from decimal import Decimal, InvalidOperation

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


@login_required(login_url='login')
def checkout_page(request):

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
    )

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart_page')

    # STOCK CHECK
    for item in cart_items:

        if item.variant.variant_stock < item.quantity:

            messages.error(
                request,
                f"{item.variant.product.product_name} has only {item.variant.variant_stock} stock left."
            )

            return redirect('cart_page')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()

   

    subtotal = Decimal('0.00')
    offer_discount = Decimal('0.00')

    for item in cart_items:

        # USE OFFER PRICE
        price = item.variant.offer_price

        # FALLBACK
        if not price:
            price = item.variant.variant_price

        item.item_total = Decimal(price) * item.quantity

        subtotal += item.item_total

        # OFFER DISCOUNT
        if item.variant.variant_price > price:

            offer_discount += (
                item.variant.variant_price - price
            ) * item.quantity

    original_subtotal = subtotal + offer_discount


    applied_coupon = None
    discount_amount = Decimal('0.00')

    coupon_id = request.session.get('coupon_id')

    today = timezone.now().date()

    if coupon_id:

        applied_coupon = Coupon.objects.filter(
            id=coupon_id,
            is_active=True,
            is_deleted=False
        ).first()

        if applied_coupon:

            used_count = Order.objects.filter(
                user=request.user,
                coupon=applied_coupon
            ).exclude(
                payment_status='Failed'
            ).count()

            # REVALIDATE
            if (
                applied_coupon.start_date > today or
                applied_coupon.end_date < today or
                subtotal < applied_coupon.min_purchase or
                used_count >= applied_coupon.usage_limit_per_user
            ):

                request.session.pop('coupon_id', None)
                request.session.pop('discount_amount', None)

                applied_coupon = None
                discount_amount = Decimal('0.00')

            else:

                # PERCENTAGE
                if applied_coupon.discount_type == 'PERCENTAGE':

                    discount_amount = (
                        subtotal *
                        applied_coupon.discount_value
                    ) / Decimal('100')

                else:

                    discount_amount = applied_coupon.discount_value

                # MAX DISCOUNT
                if (
                    applied_coupon.max_discount and
                    discount_amount > applied_coupon.max_discount
                ):

                    discount_amount = applied_coupon.max_discount

                # PREVENT OVER DISCOUNT
                if discount_amount > subtotal:
                    discount_amount = subtotal

                request.session['discount_amount'] = str(
                    discount_amount
                )

        else:

            request.session.pop('coupon_id', None)
            request.session.pop('discount_amount', None)


    if subtotal >= 500:
        delivery_charge = Decimal('0.00')
    else:
        delivery_charge = Decimal('50.00')

    tax_amount = Decimal('0.00')



    total_amount = (
        subtotal -
        discount_amount +
        delivery_charge +
        tax_amount
    )

    # NEVER NEGATIVE
    if total_amount < 0:
        total_amount = Decimal('0.00')



    available_coupons = Coupon.objects.filter(
        is_active=True,
        is_deleted=False,
        start_date__lte=today,
        end_date__gte=today
    )


    if request.method == 'POST':

        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        # ADDRESS VALIDATION
        if not address_id:

            messages.error(
                request,
                'Please select a delivery address'
            )

            return redirect('checkout')

        # PAYMENT VALIDATION
        if not payment_method:

            messages.error(
                request,
                'Please select a payment method'
            )

            return redirect('checkout')

        # COD LIMIT
        if (
            payment_method == 'COD' and
            total_amount > 1000
        ):

            messages.error(
                request,
                'Cash on Delivery is only available for orders of ₹1000 or less'
            )

            return redirect('checkout')

        address = get_object_or_404(
            Address,
            id=address_id,
            user=request.user
        )

        try:

            with transaction.atomic():

                # FINAL STOCK CHECK
                for item in cart_items:

                    variant = item.variant
                    variant.refresh_from_db()

                    if variant.variant_stock < item.quantity:

                        messages.error(
                            request,
                            f'{variant.product.product_name} has only {variant.variant_stock} stock left'
                        )

                        return redirect('checkout')

         
      

                if payment_method == 'RAZORPAY':

                    # Re-validate total amount (Issue 9)
                    if total_amount <= 0 and subtotal > 0:
                        return JsonResponse({'success': False, 'message': 'Invalid total amount for payment'})

                    razorpay_order = client.order.create({
                        "amount": int(float(total_amount) * 100),
                        "currency": "INR",
                        "payment_capture": "1"
                    })

                    request.session['checkout_address_id'] = address_id

                    return JsonResponse({
                        'success': True,
                        'razorpay': True,
                        'order_id': razorpay_order['id'],
                        'amount': int(total_amount * 100),
                        'key': settings.RAZORPAY_KEY_ID,
                        'name': 'STYLE-HUB',
                        'description': 'Order Payment',
                    })

                # CREATE ORDER FOR COD OR WALLET
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
                    coupon=applied_coupon,
                )

       

                if payment_method == 'WALLET':

                    wallet_payment = debit_wallet(
                        user=request.user,
                        amount=total_amount,
                        purpose='Order Payment',
                        order=order
                    )

                    if not wallet_payment:

                        messages.error(
                            request,
                            'Insufficient wallet balance'
                        )

                        return redirect('checkout')

                    order.payment_status = 'Completed'
                    order.order_status = 'Confirmed'
                    order.save()

            

                if payment_method == 'COD':

                    order.payment_status = 'Pending'
                    order.order_status = 'Confirmed'
                    order.save()

             

                for item in cart_items:

                    if payment_method in ['WALLET', 'COD']:
                        item_status = 'Confirmed'
                    else:
                        item_status = 'Pending'

                    price = item.variant.offer_price

                    if not price:
                        price = item.variant.variant_price

                    OrderItem.objects.create(

                        order=order,
                        variant=item.variant,
                        product_name=item.variant.product.product_name,
                        price=price,
                        quantity=item.quantity,
                        total_price=Decimal(price) * item.quantity,
                        item_status=item_status,

                    )

                    # STOCK REDUCE
                    item.variant.variant_stock -= item.quantity
                    item.variant.save()

                # REFERRAL
                process_referral_reward(request.user, order)

                # CLEAR CART
                cart_items.delete()

                # REMOVE COUPON SESSION
                request.session.pop('coupon_id', None)
                request.session.pop('discount_amount', None)

                request.session['order_id'] = order.id

                messages.success(
                    request,
                    'Order placed successfully'
                )

                return redirect('order_success')
            
        except Exception as e:

                    print("CHECKOUT ERROR")
                    print(str(e))
                    traceback.print_exc()

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

                        return JsonResponse({
                            'success': False,
                            'message': str(e)
                        })

                    messages.error(
                        request,
                        f'Something went wrong: {e}'
                    )

                    return redirect('checkout')


    context = {

        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,

        'subtotal': subtotal,
        'original_subtotal': original_subtotal,
        'offer_discount': offer_discount,

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

        address_id = request.session.get('checkout_address_id')

        if not address_id:
            return JsonResponse({
                'success': False,
                'message': 'Checkout session expired. Please try again.'
            })

        address = get_object_or_404(
            Address,
            id=address_id,
            user=request.user
        )

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Check if there is an existing failed/pending order for this razorpay_order_id
            existing_order = Order.objects.filter(razorpay_order_id=razorpay_order_id, user=request.user).first()
            if existing_order:
                with transaction.atomic():
                    # Stock validation
                    for item in existing_order.items.all():
                        variant = item.variant
                        variant.refresh_from_db()
                        if variant.variant_stock < item.quantity:
                            return JsonResponse({
                                'success': False,
                                'message': f"{variant.product.product_name} has only {variant.variant_stock} stock left."
                            })

                    existing_order.payment_status = 'Completed'
                    existing_order.order_status = 'Confirmed'
                    existing_order.razorpay_payment_id = razorpay_payment_id
                    existing_order.razorpay_signature = razorpay_signature
                    existing_order.save()

                    for item in existing_order.items.all():
                        variant = item.variant
                        variant.variant_stock -= item.quantity
                        variant.save()

                    process_referral_reward(request.user, existing_order)

                    # Clear cart
                    Cart.objects.filter(user=request.user).delete()

                    request.session.pop('coupon_id', None)
                    request.session.pop('discount_amount', None)
                    request.session.pop('checkout_address_id', None)

                    request.session['order_id'] = existing_order.id

                    return JsonResponse({
                        'success': True,
                        'redirect_url': '/orders/order_success/'
                    })

            with transaction.atomic():
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
                    'variant__product'
                )

                if not cart_items.exists():
                     return JsonResponse({'success': False, 'message': 'Cart is empty'})

                subtotal = Decimal('0.00')
                for item in cart_items:
                    price = item.variant.offer_price if item.variant.offer_price else item.variant.variant_price
                    subtotal += Decimal(price) * item.quantity

                coupon_id = request.session.get('coupon_id')
                applied_coupon = None
                discount_amount = Decimal('0.00')
                
                if coupon_id:
                    applied_coupon = Coupon.objects.filter(id=coupon_id, is_active=True, is_deleted=False).first()
                    if applied_coupon:
                        from django.utils import timezone
                        today = timezone.now().date()
                        used_count = Order.objects.filter(user=request.user, coupon=applied_coupon).exclude(payment_status='Failed').count()
                        if (
                            applied_coupon.start_date > today or
                            applied_coupon.end_date < today or
                            subtotal < applied_coupon.min_purchase or
                            used_count >= applied_coupon.usage_limit_per_user
                        ):
                            applied_coupon = None
                            discount_amount = Decimal('0.00')
                        else:
                            if applied_coupon.discount_type == 'PERCENTAGE':
                                discount_amount = (subtotal * applied_coupon.discount_value) / Decimal('100')
                            else:
                                discount_amount = applied_coupon.discount_value
                            
                            if applied_coupon.max_discount and discount_amount > applied_coupon.max_discount:
                                discount_amount = applied_coupon.max_discount
                            
                            if discount_amount > subtotal:
                                discount_amount = subtotal

                delivery_charge = Decimal('0.00') if subtotal >= 500 else Decimal('50.00')
                total_amount = subtotal - discount_amount + delivery_charge
                if total_amount < 0: total_amount = Decimal('0.00')

                order = Order.objects.create(
                    user=request.user,
                    address=address,
                    order_number=f"SH-{uuid.uuid4().hex[:10].upper()}",
                    payment_method='RAZORPAY',
                    payment_status='Completed',
                    order_status='Confirmed',
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    delivery_charge=delivery_charge,
                    total_amount=total_amount,
                    coupon=applied_coupon,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature
                )

                for item in cart_items:
                    variant = item.variant
                    price = variant.offer_price if variant.offer_price else variant.variant_price
                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        product_name=variant.product.product_name,
                        price=price,
                        quantity=item.quantity,
                        total_price=Decimal(price) * item.quantity,
                        item_status='Confirmed',
                    )
                    variant.variant_stock -= item.quantity
                    variant.save()

                process_referral_reward(request.user, order)

                cart_items.delete()

                request.session.pop('coupon_id', None)
                request.session.pop('discount_amount', None)
                request.session.pop('checkout_address_id', None)

                request.session['order_id'] = order.id

                return JsonResponse({
                    'success': True,
                    'redirect_url': '/orders/order_success/'
                })

        except Exception as e:
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

    # ---------------- REQUEST METHOD CHECK ---------------- #

    if request.method != 'POST':
        messages.error(
            request,
            'Invalid request method'
        )
        return redirect('checkout')

    # ---------------- GET COUPON CODE ---------------- #

    coupon_code = request.POST.get(
        'coupon_code',
        ''
    ).strip().upper()

    # ---------------- EMPTY COUPON CHECK ---------------- #

    if not coupon_code:

        messages.error(
            request,
            'Please enter a coupon code'
        )

        return redirect('checkout')

    # ---------------- COUPON LENGTH VALIDATION ---------------- #

    if len(coupon_code) < 3:

        messages.error(
            request,
            'Coupon code is too short'
        )

        return redirect('checkout')

    if len(coupon_code) > 20:

        messages.error(
            request,
            'Coupon code is too long'
        )

        return redirect('checkout')

    # ---------------- COUPON FORMAT VALIDATION ---------------- #

    import re

    if not re.match(r'^[A-Z0-9_-]+$', coupon_code):

        messages.error(
            request,
            'Invalid coupon code format'
        )

        return redirect('checkout')

    # ---------------- ALREADY APPLIED CHECK ---------------- #

    if request.session.get('coupon_id'):

        messages.error(
            request,
            'A coupon is already applied'
        )

        return redirect('checkout')

    # ---------------- GET COUPON ---------------- #

    coupon = Coupon.objects.filter(
        code__iexact=coupon_code,
        is_active=True,
        is_deleted=False
    ).first()

    # ---------------- INVALID COUPON ---------------- #

    if not coupon:

        messages.error(
            request,
            'Invalid coupon code'
        )

        return redirect('checkout')

    today = timezone.now().date()

    # ---------------- COUPON START DATE CHECK ---------------- #

    if coupon.start_date > today:

        messages.error(
            request,
            'This coupon is not active yet'
        )

        return redirect('checkout')

    # ---------------- COUPON EXPIRY CHECK ---------------- #

    if coupon.end_date < today:

        messages.error(
            request,
            'This coupon has expired'
        )

        return redirect('checkout')

    # ---------------- COUPON ACTIVE STATUS CHECK ---------------- #

    if not coupon.is_active:

        messages.error(
            request,
            'This coupon is inactive'
        )

        return redirect('checkout')

    # ---------------- USAGE LIMIT CHECK ---------------- #

    used_count = Order.objects.filter(
        user=request.user,
        coupon=coupon
    ).exclude(
        payment_status='Failed'
    ).count()

    if used_count >= coupon.usage_limit_per_user:

        messages.error(
            request,
            'Coupon usage limit exceeded'
        )

        return redirect('checkout')

    # ---------------- GET VALID CART ITEMS ---------------- #

    cart_items = Cart.objects.filter(
        user=request.user,
        variant__is_deleted=False,
        variant__is_active=True,
        variant__product__is_deleted=False,
        variant__product__is_active=True,
        variant__product__category__is_deleted=False,
        variant__product__category__is_active=True
    )

    # ---------------- EMPTY CART CHECK ---------------- #

    if not cart_items.exists():

        messages.error(
            request,
            'Your cart is empty'
        )

        return redirect('cart_page')

    # ---------------- SUBTOTAL CALCULATION ---------------- #

    subtotal = Decimal('0.00')

    for item in cart_items:

        # STOCK VALIDATION

        if item.quantity > item.variant.variant_stock:

            messages.error(
                request,
                f'{item.variant.product.product_name} has only {item.variant.variant_stock} items left in stock'
            )

            return redirect('cart_page')

        # PRICE VALIDATION

        price = (
            item.variant.offer_price
            if item.variant.offer_price
            else item.variant.variant_price
        )

        try:

            price = Decimal(price)

        except (InvalidOperation, TypeError):

            messages.error(
                request,
                'Invalid product price detected'
            )

            return redirect('checkout')

        # NEGATIVE PRICE CHECK

        if price <= 0:

            messages.error(
                request,
                'Invalid product price'
            )

            return redirect('checkout')

        subtotal += price * item.quantity

    # ---------------- SUBTOTAL VALIDATION ---------------- #

    if subtotal <= 0:

        messages.error(
            request,
            'Invalid cart subtotal'
        )

        return redirect('checkout')

    # ---------------- MINIMUM PURCHASE CHECK ---------------- #

    if subtotal < coupon.min_purchase:

        remaining_amount = (
            coupon.min_purchase - subtotal
        )

        messages.error(
            request,
            f'Minimum purchase amount for this coupon is ₹{coupon.min_purchase}. Add ₹{remaining_amount} more to use this coupon.'
        )

        return redirect('checkout')

    # ---------------- DISCOUNT CALCULATION ---------------- #

    try:

        if coupon.discount_type == 'PERCENTAGE':

            discount_amount = (
                subtotal * coupon.discount_value
            ) / Decimal('100')

        elif coupon.discount_type == 'FIXED':

            discount_amount = coupon.discount_value

        else:

            messages.error(
                request,
                'Invalid coupon discount type'
            )

            return redirect('checkout')

    except Exception:

        messages.error(
            request,
            'Failed to calculate discount'
        )

        return redirect('checkout')

    # ---------------- DISCOUNT VALIDATION ---------------- #

    if discount_amount <= 0:

        messages.error(
            request,
            'Invalid discount amount'
        )

        return redirect('checkout')

    # ---------------- MAX DISCOUNT CHECK ---------------- #

    if (
        coupon.max_discount and
        discount_amount > coupon.max_discount
    ):

        discount_amount = coupon.max_discount

    # ---------------- PREVENT OVER DISCOUNT ---------------- #

    if discount_amount > subtotal:

        discount_amount = subtotal

    # ---------------- FINAL PAYABLE VALIDATION ---------------- #

    final_amount = subtotal - discount_amount

    if final_amount < 0:

        messages.error(
            request,
            'Invalid final amount calculation'
        )

        return redirect('checkout')

    # ---------------- SAVE SESSION ---------------- #

    request.session['coupon_id'] = coupon.id

    request.session['discount_amount'] = str(
        round(discount_amount, 2)
    )

    request.session['applied_coupon_code'] = coupon.code

    # ---------------- SUCCESS MESSAGE ---------------- #

    messages.success(
        request,
        f'Coupon "{coupon.code}" applied successfully'
    )

    return redirect('checkout')


@login_required(login_url='login')
def remove_coupon(request):

    request.session.pop('coupon_id', None)
    request.session.pop('discount_amount', None)

    messages.success(request, 'Coupon removed successfully')
    return redirect('checkout')


@login_required(login_url='login')
def payment_failure_page(request):
    order_id = request.GET.get('order_id')
    order = None
    if order_id:
        try:
            order = Order.objects.filter(id=order_id, user=request.user).first()
        except (ValueError, TypeError):
            pass
    return render(request, 'payment_failure.html', {'order': order})


@login_required(login_url='login')
def retry_razorpay_payment(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'success': False, 'message': 'Order ID is required'})
        
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status == 'Completed':
        return JsonResponse({'success': False, 'message': 'This order is already paid.'})
        
    # Stock validation for retry
    for item in order.items.all():
        if item.variant.variant_stock < item.quantity:
            return JsonResponse({
                'success': False,
                'message': f"{item.variant.product.product_name} is out of stock (only {item.variant.variant_stock} available)."
            })
            
    try:
        # Create a new Razorpay order
        razorpay_order = client.order.create({
            "amount": int(float(order.total_amount) * 100),
            "currency": "INR",
            "payment_capture": "1"
        })
        
        # Save the new Razorpay order ID to the order
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        # Store address in session in case verify_razorpay_payment needs it
        request.session['checkout_address_id'] = order.address.id
        
        return JsonResponse({
            'success': True,
            'key': settings.RAZORPAY_KEY_ID,
            'amount': int(order.total_amount * 100),
            'order_id': razorpay_order['id'],
            'name': 'STYLE-HUB',
            'description': 'Retry Order Payment',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='login')
def create_failed_order(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if not address_id:
            return JsonResponse({'success': False, 'message': 'Address is required'})
            
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        cart_items = Cart.objects.filter(
            user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True
        ).select_related('variant', 'variant__product')
        
        if not cart_items.exists():
            return JsonResponse({'success': False, 'message': 'Cart is empty'})
            
        subtotal = Decimal('0.00')
        for item in cart_items:
            price = item.variant.offer_price if item.variant.offer_price else item.variant.variant_price
            subtotal += Decimal(price) * item.quantity
            
        coupon_id = request.session.get('coupon_id')
        applied_coupon = None
        discount_amount = Decimal('0.00')
        if coupon_id:
            applied_coupon = Coupon.objects.filter(id=coupon_id, is_active=True, is_deleted=False).first()
            if applied_coupon:
                if applied_coupon.discount_type == 'PERCENTAGE':
                    discount_amount = (subtotal * applied_coupon.discount_value) / Decimal('100')
                else:
                    discount_amount = applied_coupon.discount_value
                if applied_coupon.max_discount and discount_amount > applied_coupon.max_discount:
                    discount_amount = applied_coupon.max_discount
                if discount_amount > subtotal:
                    discount_amount = subtotal
                    
        delivery_charge = Decimal('0.00') if subtotal >= 500 else Decimal('50.00')
        total_amount = subtotal - discount_amount + delivery_charge
        if total_amount < 0: total_amount = Decimal('0.00')
        
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                address=address,
                order_number=f"SH-{uuid.uuid4().hex[:10].upper()}",
                payment_method='RAZORPAY',
                payment_status='Failed',
                order_status='Pending',
                subtotal=subtotal,
                discount_amount=discount_amount,
                delivery_charge=delivery_charge,
                total_amount=total_amount,
                coupon=applied_coupon,
                razorpay_order_id=razorpay_order_id
            )
            
            for item in cart_items:
                price = item.variant.offer_price if item.variant.offer_price else item.variant.variant_price
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    product_name=item.variant.product.product_name,
                    price=price,
                    quantity=item.quantity,
                    total_price=Decimal(price) * item.quantity,
                    item_status='Pending'
                )
            
            return JsonResponse({
                'success': True,
                'order_id': order.id
            })
            
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def process_referral_reward(user, order):

    referral = Referral.objects.filter(referred_user=user, is_referrer_rewarded=False).first()
    if referral:
        successful_orders = Order.objects.filter(user=user).exclude(order_status='Cancelled').exclude(payment_status='Failed')
        if successful_orders.count() == 1:
            credit_wallet(referral.referrer, referral.benefit_amount_referrer, f"Referral Reward for referring {user.username}", order=order)
            referral.is_referrer_rewarded = True
            referral.save()

