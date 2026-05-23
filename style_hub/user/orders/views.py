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
    return render(request, 'orderslisting.html', context)


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
        if item.variant:
            orig_price = item.variant.variant_price
            if orig_price > item.price:
                offer_discount += (orig_price - item.price) * item.quantity
    original_subtotal = order.subtotal + offer_discount

    context = {
        'order': order,
        'offer_discount': offer_discount,
        'original_subtotal': original_subtotal,
    }

    return render(request, 'ordersview.html', context)


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
    for item in order.items.all():
        if item.variant:
            orig_price = item.variant.variant_price
            if orig_price > item.price:
                offer_discount += (orig_price - item.price) * item.quantity
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
    p.drawString(3.5 * inch, y, "Qty")
    p.drawString(4.5 * inch, y, "Unit Price")
    p.drawString(5.5 * inch, y, "Total")
    p.line(1 * inch, y - 0.1 * inch, width - 1 * inch, y - 0.1 * inch)

    y -= 0.3 * inch
    p.setFont("Helvetica", 10)

    for item in order.items.all():
        size = item.variant.size if item.variant else "N/A"

        p.drawString(1 * inch, y, f"{item.product_name} ({size})")
        p.drawString(3.5 * inch, y, f"{item.quantity}")
        p.drawString(4.5 * inch, y, f"INR {item.price}")
        p.drawString(5.5 * inch, y, f"INR {item.total_price}")

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
        order_id = request.POST.get('order_id')
        item_id = request.POST.get('item_id')
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Cancellation reason is required')
            if item_id:
                item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
                return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")
            elif order_id:
                return redirect(f"{reverse('orders_view')}?order_id={order_id}")
            return redirect('user_orders_listing')

        if item_id:
            item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

            if item.item_status not in ['Pending', 'Confirmed', 'Shipped']:
                messages.error(request, f"Item cannot be cancelled in its current status: {item.item_status}")
                return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

            with transaction.atomic():
                item.item_status = 'Cancelled'
                item.reason = reason
                item.save()

                if item.variant:
                    item.variant.variant_stock += item.quantity
                    item.variant.save()

                order = item.order

                if order.payment_status == 'Completed':
                    credit_wallet(
                        user=request.user,
                        amount=item.total_price,
                        purpose='Item Cancellation Refund',
                        order=order
                    )

                if not order.items.exclude(item_status='Cancelled').exists():
                    order.order_status = 'Cancelled'

                    if order.payment_status == 'Completed':
                        order.payment_status = 'Refunded'

                    order.save()

            messages.success(request, "Item cancelled successfully. Refund added to wallet.")
            return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

        elif order_id:
            order = get_object_or_404(Order, id=order_id, user=request.user)

            if order.order_status not in ['Pending', 'Confirmed', 'Shipped']:
                messages.error(request, f"Order cannot be cancelled in its current status: {order.order_status}")
                return redirect(f"{reverse('orders_view')}?order_id={order.id}")

            with transaction.atomic():
                order.order_status = 'Cancelled'
                order.reason = reason
                order.save()

                for item in order.items.all():
                    if item.item_status != 'Cancelled':
                        item.item_status = 'Cancelled'
                        item.reason = reason
                        item.save()

                        if item.variant:
                            item.variant.variant_stock += item.quantity
                            item.variant.save()

                if order.payment_status == 'Completed':
                    credit_wallet(
                        user=request.user,
                        amount=order.total_amount,
                        purpose='Order Cancellation Refund',
                        order=order
                    )

                    order.payment_status = 'Refunded'
                    order.save()

            messages.success(request, "Order cancelled successfully. Refund added to wallet.")
            return redirect(f"{reverse('orders_view')}?order_id={order.id}")

    return render(request, 'order_cancel_success.html')


@login_required(login_url='login')
def review_writing(request):
    item_id = request.GET.get('item_id')

    if not item_id:
        messages.error(request, 'Invalid review request')
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

    if Review.objects.filter(user=request.user, order_item=order_item).exists():
        messages.error(request, 'You already reviewed this product')
        return redirect(f'/orders/orders_view/?order_id={order_item.order.id}')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not rating:
            messages.error(request, 'Please select rating')
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        if not title or not content:
            messages.error(request, 'Please fill all fields')
            return redirect(f'/orders/review_writing/?item_id={item_id}')

        review = Review.objects.create(
            user=request.user,
            product=product,
            order_item=order_item,
            rating=int(rating),
            title=title,
            content=content,
        )

        for image in request.FILES.getlist('images'):
            ReviewImage.objects.create(
                review=review,
                image=image
            )

        messages.success(request, 'Review submitted successfully')
        return redirect(f'/orders/orders_view/?order_id={order_item.order.id}')

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

            if item.item_status != 'Delivered':
                messages.error(request, "Only delivered items can be returned.")
                return redirect(f"{reverse('orders_view')}?order_id={item.order.id}")

            item.item_status = 'Return Requested'
            item.reason = reason
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