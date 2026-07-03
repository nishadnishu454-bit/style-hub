from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal, InvalidOperation
import re
from .models import Product,Offer
from admin_panel.categorymanagement.models import Category
from datetime import datetime,date



def is_admin(user):
    return user.is_authenticated and user.is_staff

# Create your views here.


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def offer_listing(request):
    search = request.GET.get('search', '')
    offers = Offer.objects.filter(is_deleted=False).order_by('-id')
    if search:
        offers = offers.filter(Q(name__icontains=search) | Q(product__product_name__icontains=search) | Q(category__category_name__icontains=search))
    
    paginator = Paginator(offers,5)
    page_number = request.GET.get('page')
    offers_page = paginator.get_page(page_number)
    
    context = {
        'offers': offers_page,
        'search': search,
    }
    return render(request, 'offer_listing.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_offer(request):

    products = Product.objects.filter(
        is_deleted=False,
        is_active=True
    )

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':

        name = request.POST.get(
            'name',
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

        start_date = request.POST.get(
            'start_date',
            ''
        ).strip()

        end_date = request.POST.get(
            'end_date',
            ''
        ).strip()

        offer_target = request.POST.get(
            'offer_target',
            ''
        ).strip()

        product_id = request.POST.get('product')

        category_id = request.POST.get('category')

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not name or
            not discount_type or
            not discount_value or
            not start_date or
            not end_date
        ):
            messages.error(
                request,
                'All fields are required'
            )
            return redirect('add_offer')

        # ---------------- OFFER NAME VALIDATIONS ---------------- #

        if len(name) < 3:
            messages.error(
                request,
                'Offer name must contain at least 3 characters'
            )
            return redirect('add_offer')

        if len(name) > 100:
            messages.error(
                request,
                'Offer name is too long'
            )
            return redirect('add_offer')

        # prevent multiple spaces
        if "  " in name:
            messages.error(
                request,
                'Offer name contains invalid spaces'
            )
            return redirect('add_offer')

        # allow letters, numbers, spaces, hyphen
        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', name):
            messages.error(
                request,
                'Offer name contains invalid characters'
            )
            return redirect('add_offer')

        # duplicate offer validation
        if Offer.objects.filter(
            name__iexact=name,
            is_deleted=False
        ).exists():

            messages.error(
                request,
                'Offer name already exists'
            )
            return redirect('add_offer')

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
            return redirect('add_offer')

        # ---------------- DISCOUNT VALUE VALIDATION ---------------- #

        try:

            discount_value = Decimal(
                discount_value
            )

            if discount_value <= 0:
                messages.error(
                    request,
                    'Discount value must be greater than 0'
                )
                return redirect('add_offer')

            # percentage validation
            if (
                discount_type == 'PERCENTAGE' and
                discount_value > 100
            ):
                messages.error(
                    request,
                    'Percentage discount cannot exceed 100%'
                )
                return redirect('add_offer')

            # fixed amount validation
            if (
                discount_type == 'FIXED' and
                discount_value > 100000
            ):
                messages.error(
                    request,
                    'Discount amount is too high'
                )
                return redirect('add_offer')

        except InvalidOperation:
            messages.error(
                request,
                'Invalid discount value'
            )
            return redirect('add_offer')

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
                return redirect('add_offer')

            # end date validation
            if e_date <= s_date:
                messages.error(
                    request,
                    'End date must be after start date'
                )
                return redirect('add_offer')

        except ValueError:
            messages.error(
                request,
                'Invalid date format (YYYY-MM-DD)'
            )
            return redirect('add_offer')

        # ---------------- OFFER TARGET VALIDATION ---------------- #

        allowed_targets = [
            'product',
            'category'
        ]

        if offer_target not in allowed_targets:
            messages.error(
                request,
                'Invalid offer target selected'
            )
            return redirect('add_offer')

        prod = None
        cat = None

        # ---------------- PRODUCT OFFER VALIDATION ---------------- #

        if offer_target == 'product':

            if not product_id:
                messages.error(
                    request,
                    'Please select a product'
                )
                return redirect('add_offer')

            prod = get_object_or_404(
                Product,
                id=product_id,
                is_deleted=False,
                is_active=True
            )

            # duplicate active offer validation
            existing_offer = Offer.objects.filter(
                product=prod,
                is_deleted=False,
                is_active=True
            )

            if existing_offer.exists():
                messages.error(
                    request,
                    'An active offer already exists for this product'
                )
                return redirect('add_offer')

        # ---------------- CATEGORY OFFER VALIDATION ---------------- #

        elif offer_target == 'category':

            if not category_id:
                messages.error(
                    request,
                    'Please select a category'
                )
                return redirect('add_offer')

            cat = get_object_or_404(
                Category,
                id=category_id,
                is_deleted=False,
                is_active=True
            )

            # duplicate active offer validation
            existing_offer = Offer.objects.filter(
                category=cat,
                is_deleted=False,
                is_active=True
            )

            if existing_offer.exists():
                messages.error(
                    request,
                    'An active offer already exists for this category'
                )
                return redirect('add_offer')

        # ---------------- CREATE OFFER ---------------- #

        Offer.objects.create(
            name=name,
            discount_type=discount_type,
            discount_value=discount_value,
            start_date=s_date,
            end_date=e_date,
            product=prod,
            category=cat,
            is_active=True
        )

        messages.success(
            request,
            'Offer created successfully'
        )

        return redirect('offer_listing')

    context = {
        'products': products,
        'categories': categories,
    }

    return render(
        request,
        'add_offer.html',
        context
    )


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_offer(request, id):

    offer = get_object_or_404(
        Offer,
        id=id,
        is_deleted=False
    )

    products = Product.objects.filter(
        is_deleted=False,
        is_active=True
    )

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':

        name = request.POST.get(
            'name',
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

        start_date = request.POST.get(
            'start_date',
            ''
        ).strip()

        end_date = request.POST.get(
            'end_date',
            ''
        ).strip()

        offer_target = request.POST.get(
            'offer_target',
            ''
        ).strip()

        product_id = request.POST.get('product')

        category_id = request.POST.get('category')

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not name or
            not discount_type or
            not discount_value or
            not start_date or
            not end_date
        ):
            messages.error(
                request,
                'All fields are required'
            )
            return redirect('edit_offer', id=id)

        # ---------------- OFFER NAME VALIDATIONS ---------------- #

        if len(name) < 3:
            messages.error(
                request,
                'Offer name must contain at least 3 characters'
            )
            return redirect('edit_offer', id=id)

        if len(name) > 100:
            messages.error(
                request,
                'Offer name is too long'
            )
            return redirect('edit_offer', id=id)

        # prevent multiple spaces
        if "  " in name:
            messages.error(
                request,
                'Offer name contains invalid spaces'
            )
            return redirect('edit_offer', id=id)

        # only letters, numbers, spaces, &, -
        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', name):
            messages.error(
                request,
                'Offer name contains invalid characters'
            )
            return redirect('edit_offer', id=id)

        # duplicate offer name validation
        if Offer.objects.filter(
            name__iexact=name,
            is_deleted=False
        ).exclude(id=id).exists():

            messages.error(
                request,
                'Offer name already exists'
            )
            return redirect('edit_offer', id=id)

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
            return redirect('edit_offer', id=id)

        # ---------------- DISCOUNT VALUE VALIDATION ---------------- #

        try:

            discount_value = Decimal(
                discount_value
            )

            if discount_value <= 0:
                messages.error(
                    request,
                    'Discount value must be greater than 0'
                )
                return redirect('edit_offer', id=id)

            # percentage validation
            if (
                discount_type == 'PERCENTAGE' and
                discount_value > 100
            ):
                messages.error(
                    request,
                    'Percentage discount cannot exceed 100%'
                )
                return redirect('edit_offer', id=id)

            # fixed validation
            if (
                discount_type == 'FIXED' and
                discount_value > 100000
            ):
                messages.error(
                    request,
                    'Discount amount is too high'
                )
                return redirect('edit_offer', id=id)

        except InvalidOperation:
            messages.error(
                request,
                'Invalid discount value'
            )
            return redirect('edit_offer', id=id)

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

            # prevent past end dates
            if e_date < today:
                messages.error(
                    request,
                    'End date cannot be in the past'
                )
                return redirect('edit_offer', id=id)

            # end date check
            if e_date <= s_date:
                messages.error(
                    request,
                    'End date must be after start date'
                )
                return redirect('edit_offer', id=id)

        except ValueError:
            messages.error(
                request,
                'Invalid date format (YYYY-MM-DD)'
            )
            return redirect('edit_offer', id=id)

        # ---------------- OFFER TARGET VALIDATION ---------------- #

        allowed_targets = [
            'product',
            'category'
        ]

        if offer_target not in allowed_targets:
            messages.error(
                request,
                'Invalid offer target selected'
            )
            return redirect('edit_offer', id=id)

        prod = None
        cat = None

        # ---------------- PRODUCT OFFER VALIDATION ---------------- #

        if offer_target == 'product':

            if not product_id:
                messages.error(
                    request,
                    'Please select a product'
                )
                return redirect('edit_offer', id=id)

            prod = get_object_or_404(
                Product,
                id=product_id,
                is_deleted=False,
                is_active=True
            )

            # prevent duplicate active product offers
            existing_offer = Offer.objects.filter(
                product=prod,
                is_deleted=False,
                is_active=True
            ).exclude(id=id)

            if existing_offer.exists():

                messages.error(
                    request,
                    'An active offer already exists for this product'
                )

                return redirect('edit_offer', id=id)

        # ---------------- CATEGORY OFFER VALIDATION ---------------- #

        elif offer_target == 'category':

            if not category_id:
                messages.error(
                    request,
                    'Please select a category'
                )
                return redirect('edit_offer', id=id)

            cat = get_object_or_404(
                Category,
                id=category_id,
                is_deleted=False,
                is_active=True
            )

            # prevent duplicate active category offers
            existing_offer = Offer.objects.filter(
                category=cat,
                is_deleted=False,
                is_active=True
            ).exclude(id=id)

            if existing_offer.exists():

                messages.error(
                    request,
                    'An active offer already exists for this category'
                )

                return redirect('edit_offer', id=id)

        # ---------------- UPDATE OFFER ---------------- #

        offer.name = name
        offer.discount_type = discount_type
        offer.discount_value = discount_value
        offer.start_date = s_date
        offer.end_date = e_date
        offer.product = prod
        offer.category = cat

        offer.save()

        # ---------------- SUCCESS MESSAGE ---------------- #

        messages.success(
            request,
            'Offer updated successfully'
        )

        return redirect('offer_listing')

    context = {
        'offer': offer,
        'products': products,
        'categories': categories,
    }

    return render(
        request,
        'edit_offer.html',
        context
    )

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_offer(request, id):
    offer = get_object_or_404(Offer, id=id, is_deleted=False)
    offer.is_deleted = True
    offer.save()
    messages.success(request, 'Offer deleted successfully')
    return redirect('offer_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def toggle_offer_status(request, id):
    offer = get_object_or_404(Offer, id=id, is_deleted=False)
    offer.is_active = not offer.is_active
    offer.save()
    messages.success(request, f'Offer status changed to {"Active" if offer.is_active else "Inactive"}')
    return redirect('offer_listing')