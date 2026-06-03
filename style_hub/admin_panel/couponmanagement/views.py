from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from decimal import Decimal

from .models import Coupon


def is_admin(user):
    return user.is_authenticated and user.is_staff


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
        
    paginator = Paginator(coupons, 10)
    page_number = request.GET.get('page')
    coupons_page = paginator.get_page(page_number)
    
    context = {
        'coupons': coupons_page,
        'search': search,
    }


    return render(request, 'coupon_listing.html', context)


from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Coupon


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_coupon(request):
    def redirect(to):
        if to == 'add_coupon':
            return render(request, 'add_coupon.html', {'old_data': request.POST})
        from django.shortcuts import redirect as dj_redirect
        return dj_redirect(to)

    if request.method == 'POST':

        code = request.POST.get(
            'code',
            ''
        ).strip().upper()

        title = request.POST.get(
            'title',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        discount_type = request.POST.get(
            'discount_type',
            ''
        ).strip()

        discount_value = request.POST.get(
            'discount_value',
            ''
        ).strip()

        min_purchase = request.POST.get(
            'min_purchase',
            ''
        ).strip()

        max_discount = request.POST.get(
            'max_discount',
            ''
        ).strip()

        usage_limit = request.POST.get(
            'usage_limit_per_user',
            ''
        ).strip()

        start_date = request.POST.get(
            'start_date',
            ''
        ).strip()

        end_date = request.POST.get(
            'end_date',
            ''
        ).strip()

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not code or
            not title or
            not discount_type or
            not discount_value or
            not start_date or
            not end_date
        ):
            messages.error(
                request,
                'All required fields must be filled'
            )
            return redirect('add_coupon')

        # ---------------- COUPON CODE VALIDATIONS ---------------- #

        # minimum length
        if len(code) < 4:
            messages.error(
                request,
                'Coupon code must contain at least 4 characters'
            )
            return redirect('add_coupon')

        # maximum length
        if len(code) > 20:
            messages.error(
                request,
                'Coupon code is too long'
            )
            return redirect('add_coupon')

        # only uppercase letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            messages.error(
                request,
                'Coupon code should contain only uppercase letters and numbers'
            )
            return redirect('add_coupon')

        # duplicate coupon validation
        if Coupon.objects.filter(code__iexact=code).exists():
            messages.error(
                request,
                'Coupon code already exists'
            )
            return redirect('add_coupon')

        # ---------------- TITLE VALIDATIONS ---------------- #

        if len(title) < 3:
            messages.error(
                request,
                'Coupon title must contain at least 3 characters'
            )
            return redirect('add_coupon')

        if len(title) > 100:
            messages.error(
                request,
                'Coupon title is too long'
            )
            return redirect('add_coupon')

        # ---------------- DESCRIPTION VALIDATIONS ---------------- #

        if description:

            if len(description) < 10:
                messages.error(
                    request,
                    'Description must contain at least 10 characters'
                )
                return redirect('add_coupon')

            if len(description) > 500:
                messages.error(
                    request,
                    'Description is too long'
                )
                return redirect('add_coupon')

        # ---------------- DISCOUNT TYPE VALIDATION ---------------- #

        allowed_discount_types = [
            'PERCENTAGE',
            'FIXED'
        ]

        if discount_type not in allowed_discount_types:
            messages.error(
                request,
                'Invalid discount type selected'
            )
            return redirect('add_coupon')

        # ---------------- DISCOUNT VALUE VALIDATION ---------------- #

        try:

            discount_val = Decimal(discount_value)

            if discount_val <= 0:
                messages.error(
                    request,
                    'Discount value must be greater than 0'
                )
                return redirect('add_coupon')

            # percentage validation
            if (
                discount_type == 'PERCENTAGE' and
                discount_val > 100
            ):
                messages.error(
                    request,
                    'Percentage discount cannot exceed 100%'
                )
                return redirect('add_coupon')

            # fixed discount validation
            if (
                discount_type == 'FIXED' and
                discount_val > 100000
            ):
                messages.error(
                    request,
                    'Fixed discount amount is too high'
                )
                return redirect('add_coupon')

        except InvalidOperation:
            messages.error(
                request,
                'Invalid discount value'
            )
            return redirect('add_coupon')

        # ---------------- MINIMUM PURCHASE VALIDATION ---------------- #

        try:

            min_purch = (
                Decimal(min_purchase)
                if min_purchase
                else Decimal('0.00')
            )

            if min_purch < 0:
                messages.error(
                    request,
                    'Minimum purchase cannot be negative'
                )
                return redirect('add_coupon')

        except InvalidOperation:
            messages.error(
                request,
                'Invalid minimum purchase value'
            )
            return redirect('add_coupon')

        # minimum purchase should be strictly greater than fixed discount
        if (
            discount_type == 'FIXED' and
            discount_val >= min_purch
        ):
            messages.error(
                request,
                'Fixed discount must be strictly less than minimum purchase amount'
            )
            return redirect('add_coupon')

        # ---------------- MAXIMUM DISCOUNT VALIDATION ---------------- #

        try:

            max_disc = (
                Decimal(max_discount)
                if max_discount
                else Decimal('0.00')
            )

            if max_disc < 0:
                messages.error(
                    request,
                    'Maximum discount cannot be negative'
                )
                return redirect('add_coupon')

            # max discount required for percentage coupons
            if (
                discount_type == 'PERCENTAGE' and
                max_disc <= 0
            ):
                messages.error(
                    request,
                    'Maximum discount is required for percentage coupons'
                )
                return redirect('add_coupon')

        except InvalidOperation:
            messages.error(
                request,
                'Invalid maximum discount value'
            )
            return redirect('add_coupon')

        # ---------------- USAGE LIMIT VALIDATION ---------------- #

        try:

            usage_lim = (
                int(usage_limit)
                if usage_limit
                else 1
            )

            if usage_lim <= 0:
                messages.error(
                    request,
                    'Usage limit per user must be at least 1'
                )
                return redirect('add_coupon')

            if usage_lim > 1000:
                messages.error(
                    request,
                    'Usage limit is too high'
                )
                return redirect('add_coupon')

        except ValueError:
            messages.error(
                request,
                'Invalid usage limit value'
            )
            return redirect('add_coupon')

        # ---------------- DATE VALIDATIONS ---------------- #

        try:

            s_date = datetime.strptime(
                start_date,
                '%Y-%m-%d'
            ).date()

            e_date = datetime.strptime(
                end_date,
                '%Y-%m-%d'
            ).date()

            today = date.today()

            # start date validation
            if s_date < today:
                messages.error(
                    request,
                    'Start date cannot be in the past'
                )
                return redirect('add_coupon')

            # end date validation
            if e_date <= s_date:
                messages.error(
                    request,
                    'End date must be after start date'
                )
                return redirect('add_coupon')

        except ValueError:
            messages.error(
                request,
                'Invalid date format'
            )
            return redirect('add_coupon')

        # ---------------- CREATE COUPON ---------------- #

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

        messages.success(
            request,
            'Coupon created successfully'
        )

        return redirect('coupon_listing')

    return render(
        request,
        'add_coupon.html'
    )
        
    return render(request, 'add_coupon.html')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_coupon(request, id):

    coupon = get_object_or_404(
        Coupon,
        id=id,
        is_deleted=False
    )

    if request.method == 'POST':
        coupon.code = request.POST.get('code', '').strip().upper()
        coupon.title = request.POST.get('title', '').strip()
        coupon.description = request.POST.get('description', '').strip()
        coupon.discount_type = request.POST.get('discount_type', '').strip()
        coupon.discount_value = request.POST.get('discount_value', '').strip()
        coupon.min_purchase = request.POST.get('min_purchase', '').strip()
        coupon.max_discount = request.POST.get('max_discount', '').strip()
        coupon.usage_limit_per_user = request.POST.get('usage_limit_per_user', '').strip()
        
        start_date = request.POST.get('start_date', '').strip()
        try:
            coupon.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            coupon.start_date = start_date
            
        end_date = request.POST.get('end_date', '').strip()
        try:
            coupon.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            coupon.end_date = end_date

    def redirect(to, id=None):
        if to == 'edit_coupon':
            return render(request, 'edit_coupon.html', {'coupon': coupon})
        from django.shortcuts import redirect as dj_redirect
        if id is not None:
            return dj_redirect(to, id=id)
        return dj_redirect(to)

    if request.method == 'POST':

        code = request.POST.get(
            'code',
            ''
        ).strip().upper()

        title = request.POST.get(
            'title',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        discount_type = request.POST.get(
            'discount_type',
            ''
        ).strip()

        discount_value = request.POST.get(
            'discount_value',
            ''
        ).strip()

        min_purchase = request.POST.get(
            'min_purchase',
            ''
        ).strip()

        max_discount = request.POST.get(
            'max_discount',
            ''
        ).strip()

        usage_limit = request.POST.get(
            'usage_limit_per_user',
            ''
        ).strip()

        start_date = request.POST.get(
            'start_date',
            ''
        ).strip()

        end_date = request.POST.get(
            'end_date',
            ''
        ).strip()

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not code or
            not title or
            not discount_type or
            not discount_value or
            not start_date or
            not end_date
        ):
            messages.error(
                request,
                'All required fields must be filled'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- COUPON CODE VALIDATIONS ---------------- #

        # minimum length
        if len(code) < 4:
            messages.error(
                request,
                'Coupon code must contain at least 4 characters'
            )
            return redirect('edit_coupon', id=id)

        # maximum length
        if len(code) > 20:
            messages.error(
                request,
                'Coupon code is too long'
            )
            return redirect('edit_coupon', id=id)

        # only uppercase letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            messages.error(
                request,
                'Coupon code should contain only uppercase letters and numbers'
            )
            return redirect('edit_coupon', id=id)

        # duplicate coupon validation
        if Coupon.objects.filter(
            code__iexact=code
        ).exclude(id=id).exists():

            messages.error(
                request,
                'Coupon code already exists'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- TITLE VALIDATIONS ---------------- #

        if len(title) < 3:
            messages.error(
                request,
                'Coupon title must contain at least 3 characters'
            )
            return redirect('edit_coupon', id=id)

        if len(title) > 100:
            messages.error(
                request,
                'Coupon title is too long'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- DESCRIPTION VALIDATIONS ---------------- #

        if description:

            if len(description) < 10:
                messages.error(
                    request,
                    'Description must contain at least 10 characters'
                )
                return redirect('edit_coupon', id=id)

            if len(description) > 500:
                messages.error(
                    request,
                    'Description is too long'
                )
                return redirect('edit_coupon', id=id)

        # ---------------- DISCOUNT TYPE VALIDATION ---------------- #

        allowed_discount_types = [
            'PERCENTAGE',
            'FIXED'
        ]

        if discount_type not in allowed_discount_types:
            messages.error(
                request,
                'Invalid discount type selected'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- DISCOUNT VALUE VALIDATION ---------------- #

        try:

            discount_val = Decimal(discount_value)

            if discount_val <= 0:
                messages.error(
                    request,
                    'Discount value must be greater than 0'
                )
                return redirect('edit_coupon', id=id)

            # percentage validation
            if (
                discount_type == 'PERCENTAGE' and
                discount_val > 100
            ):
                messages.error(
                    request,
                    'Percentage discount cannot exceed 100%'
                )
                return redirect('edit_coupon', id=id)

            # fixed discount validation
            if (
                discount_type == 'FIXED' and
                discount_val > 100000
            ):
                messages.error(
                    request,
                    'Fixed discount amount is too high'
                )
                return redirect('edit_coupon', id=id)

        except InvalidOperation:
            messages.error(
                request,
                'Invalid discount value'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- MINIMUM PURCHASE VALIDATION ---------------- #

        try:

            min_purch = (
                Decimal(min_purchase)
                if min_purchase
                else Decimal('0.00')
            )

            if min_purch < 0:
                messages.error(
                    request,
                    'Minimum purchase cannot be negative'
                )
                return redirect('edit_coupon', id=id)

        except InvalidOperation:
            messages.error(
                request,
                'Invalid minimum purchase value'
            )
            return redirect('edit_coupon', id=id)

        # minimum purchase should be strictly greater than fixed discount
        if (
            discount_type == 'FIXED' and
            discount_val >= min_purch
        ):
            messages.error(
                request,
                'Fixed discount must be strictly less than minimum purchase amount'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- MAXIMUM DISCOUNT VALIDATION ---------------- #

        try:

            max_disc = (
                Decimal(max_discount)
                if max_discount
                else Decimal('0.00')
            )

            if max_disc < 0:
                messages.error(
                    request,
                    'Maximum discount cannot be negative'
                )
                return redirect('edit_coupon', id=id)

            # required for percentage coupons
            if (
                discount_type == 'PERCENTAGE' and
                max_disc <= 0
            ):
                messages.error(
                    request,
                    'Maximum discount is required for percentage coupons'
                )
                return redirect('edit_coupon', id=id)

        except InvalidOperation:
            messages.error(
                request,
                'Invalid maximum discount value'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- USAGE LIMIT VALIDATION ---------------- #

        try:

            usage_lim = (
                int(usage_limit)
                if usage_limit
                else 1
            )

            if usage_lim <= 0:
                messages.error(
                    request,
                    'Usage limit per user must be at least 1'
                )
                return redirect('edit_coupon', id=id)

            if usage_lim > 1000:
                messages.error(
                    request,
                    'Usage limit is too high'
                )
                return redirect('edit_coupon', id=id)

        except ValueError:
            messages.error(
                request,
                'Invalid usage limit value'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- DATE VALIDATIONS ---------------- #

        try:

            s_date = datetime.strptime(
                start_date,
                '%Y-%m-%d'
            ).date()

            e_date = datetime.strptime(
                end_date,
                '%Y-%m-%d'
            ).date()

            today = date.today()

            # end date validation
            if e_date <= s_date:
                messages.error(
                    request,
                    'End date must be after start date'
                )
                return redirect('edit_coupon', id=id)

            # expired coupon validation
            if e_date < today:
                messages.error(
                    request,
                    'Coupon expiry date cannot be in the past'
                )
                return redirect('edit_coupon', id=id)

        except ValueError:
            messages.error(
                request,
                'Invalid date format'
            )
            return redirect('edit_coupon', id=id)

        # ---------------- UPDATE COUPON ---------------- #

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

        messages.success(
            request,
            'Coupon updated successfully'
        )

        return redirect('coupon_listing')

    context = {
        'coupon': coupon,
    }

    return render(
        request,
        'edit_coupon.html',
        context
    )

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
    messages.success(request, f'Coupon status changed to {"Active" if coupon.is_active else "Inactive"}')
    return redirect('coupon_listing')
