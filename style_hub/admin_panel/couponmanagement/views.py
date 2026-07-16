from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Coupon
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ---------------- LIST COUPONS ---------------- #

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def coupon_listing(request):
    search = request.GET.get('search', '')
    coupons = Coupon.objects.filter(is_deleted=False).order_by('-id')

    if search:
        coupons = coupons.filter(
            Q(code__icontains=search) |
            Q(title__icontains=search)
        )

    paginator = Paginator(coupons, 5)
    page_number = request.GET.get('page')
    coupons_page = paginator.get_page(page_number)

    return render(request, 'coupon_listing.html', {
        'coupons': coupons_page,
        'search': search,
    })



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_coupon(request):

    def redirect_back(to):
        if to == 'add_coupon':
            return render(request, 'add_coupon.html', {'old_data': request.POST})
        return redirect(to)

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

    
        if not all([code, title, discount_type, discount_value, start_date, end_date]):
            messages.error(request, 'All required fields must be filled')
            return redirect_back('add_coupon')
    

        if len(code) < 4 or len(code) > 20:
            messages.error(request, "Coupon code must be between 4 and 20 characters")
            return redirect_back('add_coupon')

        if not re.fullmatch(r'[A-Z0-9]+', code):
            messages.error(request, "Coupon code can contain only uppercase letters and numbers")
            return redirect_back('add_coupon')

        if code.isdigit():
            messages.error(request, "Coupon code cannot contain only numbers")
            return redirect_back('add_coupon')

        if Coupon.objects.filter(code__iexact=code).exists():
            messages.error(request, "Coupon code already exists")
            return redirect_back('add_coupon')
        
        if len(title) < 3 or len(title) > 100:
            messages.error(request, "Coupon title must be between 3 and 100 characters")
            return redirect_back('add_coupon')

        if title.isspace():
            messages.error(request, "Coupon title cannot be empty")
            return redirect_back('add_coupon')

        if not re.fullmatch(r"[A-Za-z0-9\s&()\-']+", title):
            messages.error(request, "Coupon title contains invalid characters")
            return redirect_back('add_coupon')

        if title.isdigit():
            messages.error(request, "Coupon title cannot contain only numbers")
            return redirect_back('add_coupon')


        if len(description) < 10:
            messages.error(request, "Description should be at least 10 characters")
            return redirect_back('add_coupon')

        if len(description) > 500:
            messages.error(request, "Description is too long")
            return redirect_back('add_coupon')

        if description.isdigit():
            messages.error(request, "Description cannot contain only numbers")
            return redirect_back('add_coupon')
    
        try:
            discount_val = Decimal(discount_value)

            if discount_val <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return redirect_back('add_coupon')

            if discount_type == 'PERCENTAGE' and discount_val > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return redirect_back('add_coupon')

            if discount_type == 'FIXED' and discount_val > 100000:
                messages.error(request, 'Fixed discount amount is too high')
                return redirect_back('add_coupon')

        except InvalidOperation:
            messages.error(request, 'Invalid discount value')
            return redirect_back('add_coupon')

    
        try:
            min_purch = Decimal(min_purchase) if min_purchase else Decimal('0.00')

            if min_purch < 0:
                messages.error(request, 'Minimum purchase cannot be negative')
                return redirect_back('add_coupon')

        except InvalidOperation:
            messages.error(request, 'Invalid minimum purchase value')
            return redirect_back('add_coupon')

        if discount_type == 'FIXED' and discount_val >= min_purch:
            messages.error(request, 'Fixed discount must be less than minimum purchase amount')
            return redirect_back('add_coupon')


        try:
            max_disc = Decimal(max_discount) if max_discount else Decimal('0.00')

            if max_disc < 0:
                messages.error(request, 'Maximum discount cannot be negative')
                return redirect_back('add_coupon')

            if discount_type == 'PERCENTAGE' and max_disc <= 0:
                messages.error(request, 'Maximum discount is required for percentage coupons')
                return redirect_back('add_coupon')

        except InvalidOperation:
            messages.error(request, 'Invalid maximum discount value')
            return redirect_back('add_coupon')

    
        try:
            usage_lim = int(usage_limit) if usage_limit else 1

            if usage_lim <= 0:
                messages.error(request, 'Usage limit per user must be at least 1')
                return redirect_back('add_coupon')

            if usage_lim > 1000:
                messages.error(request, 'Usage limit is too high')
                return redirect_back('add_coupon')

        except ValueError:
            messages.error(request, 'Invalid usage limit value')
            return redirect_back('add_coupon')

    
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if s_date < date.today():
                messages.error(request, 'Start date cannot be in the past')
                return redirect_back('add_coupon')

            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return redirect_back('add_coupon')

        except ValueError:
            messages.error(request, 'Invalid date format')
            return redirect_back('add_coupon')


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
@user_passes_test(is_admin, login_url='admin_login')
def edit_coupon(request, id):

    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    old_data = coupon
        
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
        old_data = request.POST

        context={
            'coupon':coupon,
            'old_data':old_data
        }

        if not all([code, title, discount_type, discount_value, start_date, end_date]):
            messages.error(request, 'All required fields must be filled')
            return render(request,'edit_coupon.html',context)

        if len(code) < 4:
            messages.error(request, 'Coupon code must contain at least 4 characters')
            return render(request,'edit_coupon.html',context)

        if len(code) > 20:
            messages.error(request, 'Coupon code is too long')
            return render(request,'edit_coupon.html',context)

        if not re.match(r'^[A-Z0-9]+$', code):
            messages.error(request, 'Coupon code should contain only uppercase letters and numbers')
            return render(request,'edit_coupon.html',context)

        if Coupon.objects.filter(code__iexact=code).exclude(id=id).exists():
            messages.error(request, 'Coupon code already exists')
            return render(request,'edit_coupon.html',context)

      
        if len(title) < 3:
            messages.error(request, 'Coupon title must contain at least 3 characters')
            return render(request,'edit_coupon.html',context)

        if len(title) > 100:
            messages.error(request, 'Coupon title is too long')
            return render(request,'edit_coupon.html',context)
        
        if not title.strip():
            messages.error(request, 'Coupon title cannot contain only spaces')
            return render(request, 'edit_coupon.html', context)
        
        if not re.match(r'^[A-Za-z0-9\s&()-]+$', title):
            messages.error(request,'Coupon title contains invalid characters')
            return render(request, 'edit_coupon.html', context)
        
        if title.replace(' ', '').isdigit():
            messages.error(request, 'Coupon title cannot contain only numbers')
            return render(request, 'edit_coupon.html', context)

        
        if description and (len(description) < 10 or len(description) > 500):
            messages.error(request, 'Description must be between 10 and 500 characters')
            return render(request,'edit_coupon.html',context)

        if discount_type not in ['PERCENTAGE', 'FIXED']:
            messages.error(request, 'Invalid discount type selected')
            return render(request,'edit_coupon.html',context)

       
        try:
            discount_val = Decimal(discount_value)

            if discount_val <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return render(request,'edit_coupon.html',context)

            if discount_type == 'PERCENTAGE' and discount_val > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return render(request,'edit_coupon.html',context)

            if discount_type == 'FIXED' and discount_val > 100000:
                messages.error(request, 'Fixed discount amount is too high')
                return render(request,'edit_coupon.html',context)

        except InvalidOperation:
            messages.error(request, 'Invalid discount value')
            return render(request,'edit_coupon.html',context)

       
        try:
            min_purch = Decimal(min_purchase) if min_purchase else Decimal('0.00')

            if min_purch < 0:
                messages.error(request, 'Minimum purchase cannot be negative')
                return render(request,'edit_coupon.html',context)

        except InvalidOperation:
            messages.error(request, 'Invalid minimum purchase value')
            return render(request,'edit_coupon.html',context)

        if discount_type == 'FIXED' and discount_val >= min_purch:
            messages.error(request, 'Fixed discount must be less than minimum purchase amount')
            return render(request,'edit_coupon.html',context)

       
        try:
            max_disc = Decimal(max_discount) if max_discount else Decimal('0.00')

            if max_disc < 0:
                messages.error(request, 'Maximum discount cannot be negative')
                return render(request,'edit_coupon.html',context)

            if discount_type == 'PERCENTAGE' and max_disc <= 0:
                messages.error(request, 'Maximum discount is required for percentage coupons')
                return render(request,'edit_coupon.html',context)

        except InvalidOperation:
            messages.error(request, 'Invalid maximum discount value')
            return render(request,'edit_coupon.html',context)

       
        try:
            usage_lim = int(usage_limit) if usage_limit else 1

            if usage_lim <= 0:
                messages.error(request, 'Usage limit per user must be at least 1')
                return render(request,'edit_coupon.html',context)

            if usage_lim > 1000:
                messages.error(request, 'Usage limit is too high')
                return render(request,'edit_coupon.html',context)

        except ValueError:
            messages.error(request, 'Invalid usage limit value')
            return render(request,'edit_coupon.html',context)

      
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return render(request,'edit_coupon.html',context)

        except ValueError:
            messages.error(request, 'Invalid date format')
            return render(request,'edit_coupon.html',context)

      
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

    return render(request, 'edit_coupon.html',{
        'coupon':coupon,
        'old_data':old_data
        })



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_coupon(request, id):
    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    coupon.is_deleted = True
    coupon.save()
    messages.success(request, 'Coupon deleted successfully')
    return redirect('coupon_listing')



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def toggle_coupon_status(request, id):
    coupon = get_object_or_404(Coupon, id=id, is_deleted=False)
    coupon.is_active = not coupon.is_active
    coupon.save()

    messages.success(request,f'Coupon status changed to {"Active" if coupon.is_active else "Inactive"}' )
    return redirect('coupon_listing')