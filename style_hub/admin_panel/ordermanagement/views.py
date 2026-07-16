from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from decimal import Decimal
import re
from user.orders.models import Order, OrderItem
from user.wallet.utils import credit_wallet


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def orders_listing(request):
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    payment = request.GET.get('payment', '')
    date = request.GET.get('date', '')
    sort = request.GET.get('sort', '')

    orders = Order.objects.select_related('user').prefetch_related(
        'items',
        'items__variant',
        'items__variant__product'
    )

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(items__variant__product__product_name__icontains=search) |
            Q(items__variant__color__icontains=search) |
            Q(items__variant__size__icontains=search)
        ).distinct()

    if status:
        orders = orders.filter(order_status=status)

    if payment:
        orders = orders.filter(payment_method=payment)

    if date:
        orders = orders.filter(ordered_at__date=date)

    if sort == 'oldest':
        orders = orders.order_by('ordered_at')
    elif sort == 'amount_low':
        orders = orders.order_by('total_amount')
    elif sort == 'amount_high':
        orders = orders.order_by('-total_amount')
    else:
        orders = orders.order_by('-ordered_at')

    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search': search,
        'status': status,
        'payment': payment,
        'date': date,
        'sort': sort,
    }

    return render(request, 'orderlisting.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def order_details(request, id):
    order = get_object_or_404(
        Order.objects.select_related('user', 'address'),
        id=id
    )

    order_items = OrderItem.objects.filter(order=order).select_related(
        'variant',
        'variant__product'
    )

    VALID_TRANSITIONS = {
        'Pending': ['Pending', 'Confirmed', 'Cancelled'],
        'Confirmed': ['Confirmed', 'Shipped', 'Cancelled'],
        'Shipped': ['Shipped', 'Out for Delivery', 'Cancelled'],
        'Out for Delivery': ['Out for Delivery', 'Delivered', 'Cancelled'],
        'Delivered': ['Delivered'],
        'Cancelled': ['Cancelled'],
        'Return Requested': ['Return Requested', 'Returned', 'Return Rejected'],
        'Returned': ['Returned'],
        'Return Rejected': ['Return Rejected'],
    }

    allowed_statuses = [status for status in order.ORDER_STATUS if status[0] in VALID_TRANSITIONS.get(order.order_status, [order.order_status])]

    context = {
        'order': order,
        'order_items': order_items,
        'allowed_statuses': allowed_statuses,
    }

    return render(request, 'orderdetails.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def update_status(request, id):
    order = get_object_or_404(Order, id=id)

    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        old_status = order.order_status

        if new_status == old_status:
            return redirect('order_details', id=order.id)

        VALID_TRANSITIONS = {
            'Pending': ['Pending', 'Confirmed', 'Cancelled'],
            'Confirmed': ['Confirmed', 'Shipped', 'Cancelled'],
            'Shipped': ['Shipped', 'Out for Delivery', 'Cancelled'],
            'Out for Delivery': ['Out for Delivery', 'Delivered', 'Cancelled'],
            'Delivered': ['Delivered'],
            'Cancelled': ['Cancelled'],
            'Return Requested': ['Return Requested', 'Returned', 'Return Rejected'],
            'Returned': ['Returned'],
            'Return Rejected': ['Return Rejected'],
        }

        if new_status not in VALID_TRANSITIONS.get(old_status, []):
            messages.error(request, f'Invalid status transition from {old_status} to {new_status}')
            return redirect('order_details', id=order.id)

        with transaction.atomic():
            order.order_status = new_status
            
            if new_status == 'Delivered' and order.payment_method == 'COD' and order.payment_status == 'Pending':
                order.payment_status = 'Completed'
                
            order.save()

            if new_status in ['Cancelled', 'Returned'] and old_status not in ['Cancelled', 'Returned', 'Return Requested']:
                from decimal import Decimal
                if order.payment_status in ['Completed', 'completed'] and order.total_amount > 0:
                    refund = order.total_amount.quantize(Decimal("0.01"))
                    credit_wallet(
                        user=order.user,
                        amount=refund,
                        purpose=f'Order {new_status} Refund',
                        order=order
                    )
                    order.refunded_amount = refund
                    order.payment_status = 'Refunded'

                for item in order.items.all():
                    if item.item_status not in ['Cancelled', 'Returned']:
                        active_qty = item.quantity - item.cancelled_quantity - item.returned_quantity
                        if active_qty > 0:
                            if item.variant:
                                item.variant.variant_stock += active_qty
                                item.variant.save()
                            
                            if new_status == 'Cancelled':
                                item.cancelled_quantity += active_qty
                            elif new_status == 'Returned':
                                item.returned_quantity += active_qty
                                
                        item.item_status = new_status
                        item.total_price = Decimal('0.00')
                        item.save()
                        
                order.subtotal = Decimal('0.00')
                order.discount_amount = Decimal('0.00')
                order.total_amount = Decimal('0.00')
                order.save()
            else:
                order.items.exclude(
                    item_status__in=['Cancelled', 'Returned', 'Return Requested']
                ).update(item_status=new_status)

        messages.success(request, f'Order status updated to {new_status}')
        return redirect('order_details', id=order.id)

    return redirect('orders_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def return_requests(request):
    search = request.GET.get('search', '')

    orders = Order.objects.filter(
        order_status='Return Requested'
    ).select_related('user').prefetch_related('items')

    items = OrderItem.objects.filter(
        item_status='Return Requested'
    ).exclude(
        order__order_status='Return Requested'
    ).select_related(
        'order',
        'order__user',
        'variant',
        'variant__product'
    )

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__username__icontains=search)
        )

        items = items.filter(
            Q(order__order_number__icontains=search) |
            Q(order__user__username__icontains=search)
        )

    

    for item in items:
        qty_to_return = item.quantity - item.cancelled_quantity - item.returned_quantity
        match = re.match(r'^\[Qty:\s*(\d+)\]\s*(.*)', item.reason or '')
        if match:
            qty_to_return = int(match.group(1))
        
  
        item.total_price = (item.price * Decimal(qty_to_return)).quantize(Decimal('0.01'))

    context = {
        'orders': orders,
        'items': items,
        'search': search,
    }

    return render(request, 'return_requests.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def approve_return(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        item_id = request.POST.get('item_id')

        with transaction.atomic():

            if item_id:
                item = get_object_or_404(
                    OrderItem.objects.select_related('order', 'variant'),
                    id=item_id
                )

                if item.item_status != 'Return Requested':
                    messages.error(request, 'This item is not requested for return')
                    return redirect('return_requests')

                qty_to_approve = item.remaining_quantity()
                match = re.match(r'^\[Qty:\s*(\d+)\]\s*(.*)', item.reason or '')
                if match:
                    qty_to_approve = int(match.group(1))

                item.returned_quantity += qty_to_approve
                remaining_qty = item.quantity - item.cancelled_quantity - item.returned_quantity
                if remaining_qty == 0:
                    item.item_status = 'Returned'
                else:
                    item.item_status = 'Partially Returned'

                item.total_price = item.price * remaining_qty
                item.save()

                if item.variant:
                    item.variant.variant_stock += qty_to_approve
                    item.variant.save()

                order = item.order

                
                all_inactive = True
                for order_item in order.items.all():
                    rem_qty = (
                        order_item.quantity
                        - order_item.cancelled_quantity
                        - order_item.returned_quantity
                    )
                    if rem_qty > 0:
                        all_inactive = False
                        break

                refund_amount = Decimal('0.00')

                if all_inactive:
                    if order.payment_status in ['Completed', 'completed'] or (order.payment_method == 'COD' and order.payment_status == 'Pending'):

                        refund_amount = order.total_amount.quantize(Decimal("0.01"))
                        credit_wallet(
                            user=order.user,
                            amount=refund_amount,
                            purpose='Return Refund',
                            order=order
                        )
                        order.refunded_amount = refund_amount
                        order.payment_status = 'Refunded'

                    order.order_status = 'Returned'
                    order.subtotal = Decimal('0.00')
                    order.discount_amount = Decimal('0.00')
                    order.total_amount = Decimal('0.00')
                    order.save()
                else:
                    returned_value = item.price * Decimal(qty_to_approve)
                    new_subtotal = order.subtotal - returned_value
                    
                    new_discount = Decimal('0.00')
                    if order.discount_amount > 0 and order.subtotal > 0:
                        if order.coupon and new_subtotal < order.coupon.min_purchase:
                            # Coupon is invalidated
                            new_discount = Decimal('0.00')
                        else:
                            new_discount = order.discount_amount - (
                                returned_value / order.subtotal
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

                    if (order.payment_status in ['Completed', 'completed'] or (order.payment_method == 'COD' and order.payment_status == 'Pending')) and refund_amount > 0:
                        credit_wallet(
                            user=order.user,
                            amount=refund_amount,
                            purpose='Return Refund',
                            order=order
                        )
                        order.refunded_amount += refund_amount
                        order.save(update_fields=['refunded_amount'])

                    order.subtotal = new_subtotal
                    order.discount_amount = new_discount.quantize(Decimal('0.01'))
                    order.total_amount = new_total.quantize(Decimal('0.01'))
                    order.save()

                messages.success(request, f'Return approved and refund processed for item: {item.product_name}')

            elif order_id:
                order = get_object_or_404(
                    Order.objects.prefetch_related('items__variant'),
                    id=order_id
                )

                if order.order_status != 'Return Requested':
                    messages.error(request, 'This order is not requested for return')
                    return redirect('return_requests')

                
                for item in order.items.all():
                    if item.item_status == 'Return Requested':
                        qty_to_return = item.quantity - item.cancelled_quantity - item.returned_quantity
                        item.returned_quantity += qty_to_return
                        item.item_status = 'Returned'
                        item.total_price = Decimal('0.00')
                        item.save()

                        if item.variant:
                            item.variant.variant_stock += qty_to_return
                            item.variant.save()

                if order.payment_status in ['Completed', 'completed'] or (order.payment_method == 'COD' and order.payment_status == 'Pending'):
                    refund = order.total_amount.quantize(Decimal("0.01"))

                    credit_wallet(
                        user=order.user,
                        amount=order.total_amount.quantize(Decimal('0.01')),
                        purpose='Return Refund',
                        order=order
                    )
                    order.refunded_amount = refund
                    order.payment_status = 'Refunded'

                order.order_status = 'Returned'
                order.subtotal = Decimal('0.00')
                order.discount_amount = Decimal('0.00')
                order.total_amount = Decimal('0.00')
                order.save()

                messages.success(request, f'Return approved and refund processed for order: {order.order_number}')

        return redirect('return_requests')

    return redirect('orders_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def reject_return(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        item_id = request.POST.get('item_id')

        if item_id:
            item = get_object_or_404(
                OrderItem.objects.select_related('order'),
                id=item_id
            )

            item.item_status = 'Return Rejected'
            item.save()

            order = item.order

            if order.order_status == 'Return Requested':
                order.order_status = 'Delivered'
                order.save()

            messages.info(request, f'Return rejected for item: {item.product_name}')

        elif order_id:
            order = get_object_or_404(Order, id=order_id)

            order.order_status = 'Return Rejected'
            order.save()

            for item in order.items.filter(item_status='Return Requested'):
                item.item_status = 'Return Rejected'
                item.save()

            messages.info(request, f'Return rejected for order: {order.order_number}')

        return redirect('return_requests')
    return redirect('orders_listing')