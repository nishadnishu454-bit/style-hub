from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal

from .models import Coupon


@login_required(login_url='admin_login')
def coupon_listing(request):
    search = request.GET.get('search', '')
    coupons = Coupon.objects.filter(is_deleted=False).order_by('-id')
    
    if search:
        coupons = coupons.filter(
            Q(code__icontains=search) |
            Q(title__icontains=search)
        )
        
    paginator = Paginator(coupons, 10)
    page_number = request.GET.get('page')
    coupons_page = paginator.get_page(page_number)
    
    context = {
        'coupons': coupons_page,
        'search': search,
    }
    return render(request, 'coupon_listing.html', context)


@login_required(login_url='admin_login')
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        min_purchase = request.POST.get('min_purchase', '').strip()
        max_discount = request.POST.get('max_discount', '').strip()
        usage_limit = request.POST.get('usage_limit_per_user', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        
        # Validations
        if not code or not title or not discount_type or not discount_value or not start_date or not end_date:
            messages.error(request, 'All required fields must be filled')
            return redirect('add_coupon')
            
        if Coupon.objects.filter(code__iexact=code).exists():
            messages.error(request, 'Coupon code already exists')
            return redirect('add_coupon')
            
        try:
            discount_val = Decimal(discount_value)
            if discount_val <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return redirect('add_coupon')
            if discount_type == 'PERCENTAGE' and discount_val > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return redirect('add_coupon')
        except ValueError:
            messages.error(request, 'Invalid discount value')
            return redirect('add_coupon')
            
        try:
            min_purch = Decimal(min_purchase) if min_purchase else Decimal('0.00')
            if min_purch < 0:
                messages.error(request, 'Minimum purchase cannot be negative')
                return redirect('add_coupon')
        except ValueError:
            messages.error(request, 'Invalid minimum purchase value')
            return redirect('add_coupon')
            
        try:
            max_disc = Decimal(max_discount) if max_discount else Decimal('0.00')
            if max_disc < 0:
                messages.error(request, 'Maximum discount cannot be negative')
                return redirect('add_coupon')
        except ValueError:
            messages.error(request, 'Invalid maximum discount value')
            return redirect('add_coupon')
            
        try:
            usage_lim = int(usage_limit) if usage_limit else 1
            if usage_lim <= 0:
                messages.error(request, 'Usage limit per user must be at least 1')
                return redirect('add_coupon')
        except ValueError:
            messages.error(request, 'Invalid usage limit value')
            return redirect('add_coupon')
            
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return redirect('add_coupon')
        except ValueError:
            messages.error(request, 'Invalid dates format')
            return redirect('add_coupon')
            
        Coupon.objects.create(
            code=code,
            title=title,
            description=description,
            discount_type=discount_type,
            discount_value=discount_val,
            min_purchase=min_purch,
            max_discount=max_disc,
            usage_limit_per_user=usage_lim,
            start_date=s_date,
            end_date=e_date,
            is_active=True
        )
        messages.success(request, 'Coupon created successfully')
        return redirect('coupon_listing')
        
    return render(request, 'add_coupon.html')


@login_required(login_url='admin_login')
def edit_coupon(request, id):
    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        min_purchase = request.POST.get('min_purchase', '').strip()
        max_discount = request.POST.get('max_discount', '').strip()
        usage_limit = request.POST.get('usage_limit_per_user', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        
        # Validations
        if not code or not title or not discount_type or not discount_value or not start_date or not end_date:
            messages.error(request, 'All required fields must be filled')
            return redirect('edit_coupon', id=id)
            
        if Coupon.objects.filter(code__iexact=code).exclude(id=id).exists():
            messages.error(request, 'Coupon code already exists')
            return redirect('edit_coupon', id=id)
            
        try:
            discount_val = Decimal(discount_value)
            if discount_val <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return redirect('edit_coupon', id=id)
            if discount_type == 'PERCENTAGE' and discount_val > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return redirect('edit_coupon', id=id)
        except ValueError:
            messages.error(request, 'Invalid discount value')
            return redirect('edit_coupon', id=id)
            
        try:
            min_purch = Decimal(min_purchase) if min_purchase else Decimal('0.00')
            if min_purch < 0:
                messages.error(request, 'Minimum purchase cannot be negative')
                return redirect('edit_coupon', id=id)
        except ValueError:
            messages.error(request, 'Invalid minimum purchase value')
            return redirect('edit_coupon', id=id)
            
        try:
            max_disc = Decimal(max_discount) if max_discount else Decimal('0.00')
            if max_disc < 0:
                messages.error(request, 'Maximum discount cannot be negative')
                return redirect('edit_coupon', id=id)
        except ValueError:
            messages.error(request, 'Invalid maximum discount value')
            return redirect('edit_coupon', id=id)
            
        try:
            usage_lim = int(usage_limit) if usage_limit else 1
            if usage_lim <= 0:
                messages.error(request, 'Usage limit per user must be at least 1')
                return redirect('edit_coupon', id=id)
        except ValueError:
            messages.error(request, 'Invalid usage limit value')
            return redirect('edit_coupon', id=id)
            
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return redirect('edit_coupon', id=id)
        except ValueError:
            messages.error(request, 'Invalid dates format')
            return redirect('edit_coupon', id=id)
            
        coupon.code = code
        coupon.title = title
        coupon.description = description
        coupon.discount_type = discount_type
        coupon.discount_value = discount_val
        coupon.min_purchase = min_purch
        coupon.max_discount = max_disc
        coupon.usage_limit_per_user = usage_lim
        coupon.start_date = s_date
        coupon.end_date = e_date
        coupon.save()
        
        messages.success(request, 'Coupon updated successfully')
        return redirect('coupon_listing')
        
    context = {
        'coupon': coupon,
    }
    return render(request, 'edit_coupon.html', context)


@login_required(login_url='admin_login')
def delete_coupon(request, id):
    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    coupon.is_deleted = True
    coupon.save()
    messages.success(request, 'Coupon deleted successfully')
    return redirect('coupon_listing')


@login_required(login_url='admin_login')
def toggle_coupon_status(request, id):
    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    coupon.is_active = not coupon.is_active
    coupon.save()
    messages.success(request, f'Coupon status changed to {"Active" if coupon.is_active else "Inactive"}')
    return redirect('coupon_listing')
