from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction

from user.orders.models import Order, OrderItem
from admin_panel.productmanagement.models import ProductVariant


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

    context = {
        'order': order,
        'order_items': order_items,
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

        with transaction.atomic():
            order.order_status = new_status
            order.save()

            # If order is cancelled or returned, revert stock for all items that weren't already cancelled/returned
            if new_status in ['Cancelled', 'Returned'] and old_status not in ['Cancelled', 'Returned', 'Return Requested']:
                for item in order.items.all():
                    if item.item_status not in ['Cancelled', 'Returned']:
                        if item.variant:
                            item.variant.variant_stock += item.quantity
                            item.variant.save()
                        item.item_status = new_status
                        item.save()
            else:
                # Update individual item statuses to match the new order status
                # (Assuming admin status change applies to all items unless they were manually changed)
                order.items.exclude(item_status__in=['Cancelled', 'Returned', 'Return Requested']).update(item_status=new_status)

        messages.success(request, f'Order status updated to {new_status}')
        return redirect('order_details', id=order.id)

    return redirect('orders_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def return_requests(request):
    search = request.GET.get('search', '')
    
    # Filter for orders or items that have "Return Requested" status
    orders = Order.objects.filter(order_status='Return Requested').select_related('user').prefetch_related('items')
    items = OrderItem.objects.filter(item_status='Return Requested').select_related('order', 'order__user', 'variant', 'variant__product')

    if search:
        orders = orders.filter(Q(order_number__icontains=search) | Q(user__username__icontains=search))
        items = items.filter(Q(order__order_number__icontains=search) | Q(order__user__username__icontains=search))

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
                item = get_object_or_404(OrderItem, id=item_id)
                item.item_status = 'Returned'
                item.save()
                if item.variant:
                    item.variant.variant_stock += item.quantity
                    item.variant.save()
                
                # Update order status if all items are now Returned/Cancelled
                order = item.order
                if not order.items.exclude(item_status__in=['Returned', 'Cancelled']).exists():
                    order.order_status = 'Returned'
                    order.save()
                
                messages.success(request, f"Return approved for item: {item.product_name}")
            
            elif order_id:
                order = get_object_or_404(Order, id=order_id)
                order.order_status = 'Returned'
                order.save()
                for item in order.items.all():
                    if item.item_status == 'Return Requested':
                        item.item_status = 'Returned'
                        item.save()
                        if item.variant:
                            item.variant.variant_stock += item.quantity
                            item.variant.save()
                
                messages.success(request, f"Return approved for order: {order.order_number}")

        return redirect('return_requests')
    return redirect('orders_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def reject_return(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        item_id = request.POST.get('item_id')

        if item_id:
            item = get_object_or_404(OrderItem, id=item_id)
            item.item_status = 'Return Rejected'
            item.save()
            
            # Reset order status if it was Return Requested
            order = item.order
            if order.order_status == 'Return Requested':
                order.order_status = 'Delivered'
                order.save()
                
            messages.info(request, f"Return rejected for item: {item.product_name}")
        
        elif order_id:
            order = get_object_or_404(Order, id=order_id)
            order.order_status = 'Return Rejected'
            order.save()
            for item in order.items.filter(item_status='Return Requested'):
                item.item_status = 'Return Rejected'
                item.save()
                
            messages.info(request, f"Return rejected for order: {order.order_number}")

        return redirect('return_requests')
    return redirect('orders_listing')