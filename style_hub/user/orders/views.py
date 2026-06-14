from django.db import transaction
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from django.http import HttpResponse
from django.db.models import Q
from user.orders.models import Order, OrderItem, Review, ReviewImage
from user.wallet.utils import credit_wallet
from decimal import Decimal
import re


@login_required(login_url='login')
def user_orders_listing(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items',
        'items__variant',
        'items__variant__product',
        'items__variant__images'
    ).order_by('-ordered_at')

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()

    if status_filter:
        orders = orders.filter(order_status=status_filter)

    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request,'orderslisting.html', context)


@login_required(login_url='login')
def orders_view(request):
    order_id = request.GET.get('order_id')

    if not order_id:
        return redirect('user_orders_listing')

    order = get_object_or_404(
        Order.objects.select_related('address').prefetch_related(
            'items',
            'items__variant',
            'items__variant__product',
            'items__variant__images'
        ),
        id=order_id,
        user=request.user
    )

    from decimal import Decimal
    offer_discount = Decimal('0.00')
    for item in order.items.all():
        active_qty = item.quantity - item.cancelled_quantity - item.returned_quantity
        if active_qty > 0 and item.variant:
            orig_price = item.variant.variant_price
            if orig_price > item.price:
                offer_discount += (orig_price - item.price) * active_qty
    original_subtotal = order.subtotal + offer_discount

    context = {
        'order': order,
        'offer_discount': offer_discount,
        'original_subtotal': original_subtotal,
    }

    return render(request, 'ordersview.html', context)


from django.views.decorators.cache import never_cache

@never_cache
@login_required(login_url='login')
def order_success(request):
    order_id = request.session.get('order_id')

    if not order_id:
        messages.error(request, 'No recent order found')
        return redirect('home')

    order = get_object_or_404(
        Order.objects.select_related('user', 'address').prefetch_related(
            'items',
            'items__variant',
            'items__variant__product'
        ),
        id=order_id,
        user=request.user
    )

    return render(request, 'ordersuccess.html', {'order': order})


@login_required(login_url='login')
def invoice(request):
    order_id = request.GET.get('order_id')

    order = get_object_or_404(
        Order.objects.select_related('address').prefetch_related(
            'items',
            'items__variant'
        ),
        id=order_id,
        user=request.user
    )

    from decimal import Decimal
    offer_discount = Decimal('0.00')
    # Filter active items to recalculate correct original subtotal and offer discounts using active quantities
    for item in order.items.all():
        active_qty = item.quantity - item.cancelled_quantity - item.returned_quantity
        if active_qty > 0 and item.variant:
            orig_price = item.variant.variant_price
            if orig_price > item.price:
                offer_discount += (orig_price - item.price) * active_qty
    original_subtotal = order.subtotal + offer_discount

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, height - 1 * inch, "STYLE-HUB")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2, height - 1.3 * inch, "The Midnight Atelier")

    p.line(1 * inch, height - 1.5 * inch, width - 1 * inch, height - 1.5 * inch)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 2 * inch, f"Invoice Number: #INV-{order.order_number}")
    p.drawString(1 * inch, height - 2.2 * inch, f"Order Date: {order.ordered_at.strftime('%B %d, %Y')}")

    p.drawString(1 * inch, height - 2.7 * inch, "Bill To:")
    p.setFont("Helvetica", 10)

    addr = order.address

    if addr:
        p.drawString(1 * inch, height - 2.9 * inch, f"{addr.full_name}")
        p.drawString(1 * inch, height - 3.1 * inch, f"{addr.house_name}, {addr.address}")
        p.drawString(1 * inch, height - 3.3 * inch, f"{addr.area}, {addr.district}")
        p.drawString(1 * inch, height - 3.5 * inch, f"{addr.state}, {addr.pincode}")
    else:
        p.drawString(1 * inch, height - 2.9 * inch, "N/A")

    y = height - 4.2 * inch
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1 * inch, y, "Product Name")
    p.drawString(3.5 * inch, y, "active_qty")
    p.drawString(4.5 * inch, y, "Unit Price")
    p.drawString(5.5 * inch, y, "Total")
    p.line(1 * inch, y - 0.1 * inch, width - 1 * inch, y - 0.1 * inch)

    y -= 0.3 * inch
    p.setFont("Helvetica", 10)

    for item in order.items.all():
        size = item.variant.size if item.variant else "N/A"
        active_qty = (item.quantity - item.cancelled_quantity - item.returned_quantity)
        status_suffix = ""
        active_total = item.price * active_qty
        item_total_str = f"INR {active_total}"

        if active_qty == 0:
            if item.returned_quantity == item.quantity:
                status_suffix = " [Returned]"
                item_total_str = "Returned"
            else:
                status_suffix = " [Cancelled]"
                item_total_str = "Cancelled"
        elif item.item_status == 'Return Requested':
            status_suffix = " [Return Req]"
        elif item.item_status == 'Partially Cancelled':
            status_suffix = " [Partially Cancelled]"
        elif item.item_status == 'Partially Returned':
            status_suffix = " [Partially Returned]"

        p.drawString(1 * inch, y, f"{item.product_name} ({size}){status_suffix}")
        p.drawString(3.5 * inch, y, f"{active_qty}")
        p.drawString(4.5 * inch, y, f"INR {item.price}")
        p.drawString(5.5 * inch, y, item_total_str)

        y -= 0.25 * inch

        if y < 1 * inch:
            p.showPage()
            y = height - 1 * inch

    y -= 0.2 * inch
    p.line(4 * inch, y, width - 1 * inch, y)

    y -= 0.3 * inch
    p.drawString(4.5 * inch, y, "Subtotal:")
    p.drawRightString(width - 1 * inch, y, f"INR {original_subtotal}")

    if offer_discount > 0:
        y -= 0.2 * inch
        p.drawString(4.5 * inch, y, "Offer Discount:")
        p.drawRightString(width - 1 * inch, y, f"- INR {offer_discount}")

    if order.discount_amount > 0:
        y -= 0.2 * inch
        p.drawString(4.5 * inch, y, "Coupon Discount:")
        p.drawRightString(width - 1 * inch, y, f"- INR {order.discount_amount}")

    y -= 0.2 * inch
    p.drawString(4.5 * inch, y, "Delivery:")
    p.drawRightString(width - 1 * inch, y, f"INR {order.delivery_charge}")

    y -= 0.3 * inch
    p.setFont("Helvetica-Bold", 12)
    p.drawString(4.5 * inch, y, "Final Total:")
    p.drawRightString(width - 1 * inch, y, f"INR {order.total_amount}")

    p.showPage()
    p.save()

    return response


@login_required(login_url='login')
def order_cancel_success(request):

    if request.method == 'POST':

        item_id = request.POST.get('item_id')
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Cancellation reason is required')
            return redirect('user_orders_listing')

        item = get_object_or_404(
            OrderItem,
            id=item_id,
            order__user=request.user
        )

        cancel_quantity = int(request.POST.get('cancel_quantity', request.POST.get('quantity', 0)))

        if cancel_quantity <= 0:
            messages.error(request, 'Invalid cancel quantity')
            return redirect(
                f"{reverse('orders_view')}?order_id={item.order.id}"
            )

        if item.item_status not in [
            'Pending',
            'Confirmed',
            'Shipped',
            'Partially Cancelled'
        ]:
            messages.error(
                request,
                f"Item cannot be cancelled: {item.item_status}"
            )
            return redirect(
                f"{reverse('orders_view')}?order_id={item.order.id}"
            )

        available_quantity = (
            item.quantity
            - item.cancelled_quantity
            - item.returned_quantity
        )

        if cancel_quantity > available_quantity:
            messages.error(
                request,
                'Cancel quantity exceeds available quantity'
            )
            return redirect(
                f"{reverse('orders_view')}?order_id={item.order.id}"
            )

        with transaction.atomic():

            # UPDATE CANCELLED QTY
            item.cancelled_quantity += cancel_quantity
            item.reason = reason

            remaining_quantity = (
                item.quantity
                - item.cancelled_quantity
                - item.returned_quantity
            )

            # STATUS UPDATE
            if remaining_quantity == 0:
                item.item_status = 'Cancelled'
            else:
                item.item_status = f'Partially Cancelled ({item.cancelled_quantity})'

            item.total_price = item.price * remaining_quantity
            item.save()

            # STOCK RETURN
            if item.variant:
                item.variant.variant_stock += cancel_quantity
                item.variant.save()

            order = item.order

            # FULL ORDER CANCEL CHECK
            all_cancelled = True
            for order_item in order.items.all():
                rem_qty = (
                    order_item.quantity
                    - order_item.cancelled_quantity
                    - order_item.returned_quantity
                )
                if rem_qty > 0:
                    all_cancelled = False
                    break

            refund_amount = Decimal('0.00')

            if all_cancelled:
                # Refund the remaining total amount of the order (including delivery charge)
                if order.payment_status == 'Completed':
                    refund_amount = order.total_amount.quantize(Decimal('0.01'))
                    credit_wallet(
                        user=request.user,
                        amount=refund_amount,
                        purpose='Item Cancellation Refund',
                        order=order
                    )
                    order.payment_status = 'Refunded'

                order.order_status = 'Cancelled'
                order.subtotal = Decimal('0.00')
                order.discount_amount = Decimal('0.00')
                order.total_amount = Decimal('0.00')
                order.save()
            else:
                cancelled_total = item.price * Decimal(cancel_quantity)
                new_subtotal = order.subtotal - cancelled_total
                
                new_discount = Decimal('0.00')
                if order.discount_amount > 0 and order.subtotal > 0:
                    if order.coupon and new_subtotal < order.coupon.min_purchase:
                        # Coupon is invalidated
                        new_discount = Decimal('0.00')
                    else:
                        new_discount = order.discount_amount - (
                            cancelled_total / order.subtotal
                        ) * order.discount_amount

                new_total = max(
                    new_subtotal
                    - new_discount
                    + order.delivery_charge,
                    Decimal('0.00')
                )

                refund_amount = order.total_amount - new_total
                if refund_amount < 0:
                    refund_amount = Decimal('0.00')
                    new_total = order.total_amount

                refund_amount = refund_amount.quantize(Decimal('0.01'))

                if order.payment_status == 'Completed' and refund_amount > 0:
                    credit_wallet(
                        user=request.user,
                        amount=refund_amount,
                        purpose='Item Cancellation Refund',
                        order=order
                    )

                order.subtotal = new_subtotal
                order.discount_amount = new_discount.quantize(Decimal('0.01'))
                order.total_amount = new_total.quantize(Decimal('0.01'))
                order.save()

        context = {
            'cancelled_item': [item],
            'cancelled_order': order,
            'refund_amount': refund_amount,
            'cancel_quantity': cancel_quantity,
            'cancel_type': 'item',
        }

        return render(
            request,
            'order_cancel_success.html',
            context
        )

    return redirect('user_orders_listing')

@login_required(login_url='login')
def review_writing(request):

    item_id = request.GET.get('item_id')

    if not item_id:
        messages.error(request, 'Invalid review request')
        return redirect('user_orders_listing')

    # ITEM VALIDATION
    if not str(item_id).isdigit():
        messages.error(request, 'Invalid order item')
        return redirect('user_orders_listing')

    order_item = get_object_or_404(
        OrderItem.objects.select_related(
            'order',
            'variant',
            'variant__product',
            'variant__product__category'
        ),
        id=item_id,
        order__user=request.user
    )

    product = order_item.variant.product

    # PRODUCT STATUS VALIDATION
    if (
        product.is_deleted or
        not product.is_active or
        order_item.variant.is_deleted or
        not order_item.variant.is_active
    ):
        messages.error(request, 'This product is unavailable for review')
        return redirect(
            f"{reverse('orders_view')}?order_id={order_item.order.id}"
        )

    # ONLY DELIVERED PRODUCTS
    if order_item.item_status not in ['Delivered', 'Partially Returned', 'Return Rejected']:
        messages.error(request, 'Review can only be added for delivered products')
        return redirect(
            f"{reverse('orders_view')}?order_id={order_item.order.id}"
        )

    # PREVENT DUPLICATE REVIEW
    if Review.objects.filter(
        user=request.user,
        order_item=order_item
    ).exists():

        messages.error(request, 'You already reviewed this product')

        return redirect(
            f"{reverse('orders_view')}?order_id={order_item.order.id}"
        )

    if request.method == 'POST':

        rating = request.POST.get('rating', '').strip()
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        images = request.FILES.getlist('images')

        # REQUIRED FIELD VALIDATION
        if not rating or not title or not content:
            messages.error(request, 'Please fill all fields')
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # RATING VALIDATION
        try:
            rating = int(rating)

            if rating < 1 or rating > 5:
                messages.error(request, 'Rating must be between 1 and 5')
                return redirect(f'/orders/review_writing/?item_id={item_id}')

        except ValueError:
            messages.error(request, 'Invalid rating')
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # TITLE LENGTH VALIDATION
        if len(title) < 3:
            messages.error(
                request,
                'Review title must contain at least 3 characters'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        if len(title) > 100:
            messages.error(
                request,
                'Review title cannot exceed 100 characters'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # CONTENT LENGTH VALIDATION
        if len(content) < 10:
            messages.error(
                request,
                'Review content must contain at least 10 characters'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        if len(content) > 1000:
            messages.error(
                request,
                'Review content cannot exceed 1000 characters'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # INVALID SPACES
        if "  " in title:
            messages.error(
                request,
                'Review title contains invalid spaces'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # TITLE CHARACTER VALIDATION
        if not re.match(r'^[A-Za-z0-9\s.,!?&()\'"-]+$', title):
            messages.error(
                request,
                'Review title contains invalid characters'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # IMAGE LIMIT VALIDATION
        if len(images) > 3:
            messages.error(
                request,
                'Maximum 3 review images are allowed'
            )
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        # IMAGE VALIDATION
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']

        for image in images:

            # FILE SIZE VALIDATION
            if image.size > 5 * 1024 * 1024:
                messages.error(
                    request,
                    'Each image must be less than 5MB'
                )
                return redirect(f'/orders/review_writing/?item_id={item_id}')

            # EXTENSION VALIDATION
            extension = image.name.split('.')[-1].lower()

            if extension not in allowed_extensions:
                messages.error(
                    request,
                    'Only JPG, JPEG, PNG and WEBP images are allowed'
                )
                return redirect(f'/orders/review_writing/?item_id={item_id}')

        # CREATE REVIEW
        review = Review.objects.create(
            user=request.user,
            product=product,
            order_item=order_item,
            rating=rating,
            title=title,
            content=content,
        )

        # SAVE REVIEW IMAGES
        for image in images:

            ReviewImage.objects.create(
                review=review,
                image=image
            )

        messages.success(request, 'Review submitted successfully')

        return redirect(
            f'/orders/orders_view/?order_id={order_item.order.id}'
        )

    context = {
        'product': product,
        'order_item': order_item,
    }

    return render(request, 'review_writing.html', context)

@login_required(login_url='login')
def return_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        item_id = request.POST.get('item_id')
        reason = request.POST.get('reason')

        if not reason:
            messages.error(request, "Return reason is required.")
            return redirect('user_orders_listing')

        if item_id:
            item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

            if item.item_status not in ['Delivered', 'Partially Returned', 'Return Rejected']:
                messages.error(request, "Only delivered or partially returned items can be returned.")
                return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

            quantity_to_return = int(request.POST.get('quantity', 1))
            available_qty = item.quantity - item.cancelled_quantity - item.returned_quantity
            if quantity_to_return <= 0 or quantity_to_return > available_qty:
                messages.error(request, "Invalid return quantity.")
                return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

            item.item_status = 'Return Requested'
            item.reason = f"[Qty: {quantity_to_return}] {reason}"
            item.save()

            order = item.order

            if not order.items.exclude(
                item_status__in=['Return Requested', 'Returned', 'Cancelled']
            ).exists():
                order.order_status = 'Return Requested'
                order.save()

            messages.success(request, "Return request submitted successfully.")
            return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

        elif order_id:
            order = get_object_or_404(Order, id=order_id, user=request.user)

            if order.order_status != 'Delivered':
                messages.error(request, "Only delivered orders can be returned.")
                return redirect(f"{reverse('orders_view')}?order_id={order.id}")

            order.order_status = 'Return Requested'
            order.reason = reason
            order.save()

            for item in order.items.all():
                if item.item_status == 'Delivered':
                    item.item_status = 'Return Requested'
                    item.reason = reason
                    item.save()

            messages.success(request, "Order return request submitted successfully.")
            return redirect(f"{reverse('orders_view')}?order_id={order.id}")

    return redirect('user_orders_listing')