from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test


def is_admin(user):
    return user.is_authenticated and user.is_staff

from django.core.files.base import ContentFile
from django.db.models import Sum
import base64
from decimal import Decimal, InvalidOperation
import re
from .models import Product, ProductVariant, ProductVariantImage, Offer
from admin_panel.categorymanagement.models import Category
from datetime import datetime,date


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def product_listing(request):
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', '')

    products = Product.objects.filter(
        is_deleted=False
    ).select_related('category').order_by('-id')

    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(category__category_name__icontains=search)
        )

    if sort == 'oldest':
        products = products.order_by('id')
    elif sort == 'name_asc':
        products = products.order_by('product_name')
    elif sort == 'name_desc':
        products = products.order_by('-product_name')
    else:
        products = products.order_by('-id')

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'search': search,
        'sort': sort,
    }

    return render(request, 'productlisting.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_product(request):

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':

        product_name = request.POST.get(
            'product_name',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        category_id = request.POST.get(
            'category'
        )

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not product_name or
            not description or
            not category_id
        ):
            messages.error(
                request,
                'All fields are required'
            )
            return redirect('add_product')

        # ---------------- PRODUCT NAME VALIDATIONS ---------------- #

        # minimum length
        if len(product_name) < 3:
            messages.error(
                request,
                'Product name must contain at least 3 characters'
            )
            return redirect('add_product')

        # maximum length
        if len(product_name) > 100:
            messages.error(
                request,
                'Product name is too long'
            )
            return redirect('add_product')

        # prevent multiple spaces
        if "  " in product_name:
            messages.error(
                request,
                'Product name contains invalid spaces'
            )
            return redirect('add_product')

        # only letters, numbers and spaces
        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', product_name):
            messages.error(
                request,
                'Product name contains invalid characters'
            )
            return redirect('add_product')

        # duplicate product validation
        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False
        ).exists():

            messages.error(
                request,
                'Product already exists'
            )
            return redirect('add_product')

        # ---------------- DESCRIPTION VALIDATIONS ---------------- #

        # minimum length
        if len(description) < 10:
            messages.error(
                request,
                'Description must contain at least 10 characters'
            )
            return redirect('add_product')

        # maximum length
        if len(description) > 2000:
            messages.error(
                request,
                'Description is too long'
            )
            return redirect('add_product')

        # prevent meaningless descriptions
        if description.isdigit():
            messages.error(
                request,
                'Description cannot contain only numbers'
            )
            return redirect('add_product')

        # ---------------- CATEGORY VALIDATIONS ---------------- #

        try:

            category = get_object_or_404(
                Category,
                id=category_id,
                is_deleted=False,
                is_active=True
            )

        except:

            messages.error(
                request,
                'Invalid category selected'
            )
            return redirect('add_product')

        # ---------------- CREATE PRODUCT ---------------- #

        Product.objects.create(
            product_name=product_name,
            description=description,
            category=category,
        )

        messages.success(
            request,
            'Product added successfully'
        )

        return redirect('product_listing')

    context = {
        'categories': categories
    }

    return render(
        request,
        'addproduct.html',
        context
    )

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_product(request, id):

    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False
    )

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':

        product_name = request.POST.get(
            'product_name',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        category_id = request.POST.get(
            'category'
        )

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not product_name or
            not description or
            not category_id
        ):
            messages.error(
                request,
                'All fields are required'
            )
            return redirect('edit_product', id=id)

        # ---------------- PRODUCT NAME VALIDATIONS ---------------- #

        # minimum length
        if len(product_name) < 3:
            messages.error(
                request,
                'Product name must contain at least 3 characters'
            )
            return redirect('edit_product', id=id)

        # maximum length
        if len(product_name) > 100:
            messages.error(
                request,
                'Product name is too long'
            )
            return redirect('edit_product', id=id)

        # prevent multiple spaces
        if "  " in product_name:
            messages.error(
                request,
                'Product name contains invalid spaces'
            )
            return redirect('edit_product', id=id)

        # only letters, numbers, spaces, hyphen and &
        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', product_name):
            messages.error(
                request,
                'Product name contains invalid characters'
            )
            return redirect('edit_product', id=id)

        # duplicate product validation
        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False
        ).exclude(id=id).exists():

            messages.error(
                request,
                'Product already exists'
            )
            return redirect('edit_product', id=id)

        # ---------------- DESCRIPTION VALIDATIONS ---------------- #

        # minimum length
        if len(description) < 20:
            messages.error(
                request,
                'Description must contain at least 20 characters'
            )
            return redirect('edit_product', id=id)

        # maximum length
        if len(description) > 2000:
            messages.error(
                request,
                'Description is too long'
            )
            return redirect('edit_product', id=id)

        # prevent numeric-only description
        if description.isdigit():
            messages.error(
                request,
                'Description cannot contain only numbers'
            )
            return redirect('edit_product', id=id)

        # prevent repeated invalid spaces
        if "  " in description:
            messages.error(
                request,
                'Description contains invalid spaces'
            )
            return redirect('edit_product', id=id)

        # ---------------- CATEGORY VALIDATIONS ---------------- #

        try:

            category = get_object_or_404(
                Category,
                id=category_id,
                is_deleted=False,
                is_active=True
            )

        except:

            messages.error(
                request,
                'Invalid category selected'
            )
            return redirect('edit_product', id=id)

        # ---------------- UPDATE PRODUCT ---------------- #

        product.product_name = product_name
        product.description = description
        product.category = category

        product.save()

        messages.success(
            request,
            'Product updated successfully'
        )

        return redirect('product_listing')

    context = {
        'product': product,
        'categories': categories,
    }

    return render(
        request,
        'editproduct.html',
        context
    )

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def view_product(request, id):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'variants',
            'variants__images'
        ),
        id=id,
        is_deleted=False
    )

    total_stock = product.variants.filter(is_deleted=False).aggregate(total=Sum('variant_stock'))['total'] or 0 

    context = {
        'product': product,
        'total_stock':total_stock
    }

    return render(request, 'viewproduct.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def activate_product(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False
    )

    product.is_active = True
    product.save()

    messages.success(request, 'Product activated successfully')
    return redirect('view_product', id=product.id)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def deactivate_product(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False
    )

    product.is_active = False
    product.save()

    messages.success(request, 'Product deactivated successfully')
    return redirect('view_product', id=product.id)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_product(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False
    )

    product.is_deleted = True
    product.save()

    messages.success(request, 'Product deleted successfully')
    return redirect('product_listing')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def variant_management(request):
    search = request.GET.get('search', '')

    products = Product.objects.filter(
        is_deleted=False
    ).select_related('category').prefetch_related(
        'variants',
        'variants__images'
    ).order_by('-id')

    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(category__category_name__icontains=search)
        )

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'search': search,
    }

    return render(request, 'variant_management.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_variant(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_deleted=False
    )

    if request.method == 'POST':

        size = request.POST.get(
            'size',
            ''
        ).strip()

        color = request.POST.get(
            'color',
            ''
        ).strip()

        price = request.POST.get(
            'variant_price',
            ''
        ).strip()

        stock = request.POST.get(
            'variant_stock',
            ''
        ).strip()

        cropped_images = [
            request.POST.get('variant_cropped_image_1'),
            request.POST.get('variant_cropped_image_2'),
            request.POST.get('variant_cropped_image_3')
        ]

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not size or
            not color or
            not price or
            not stock
        ):
            messages.error(
                request,
                'All variant details are required'
            )
            return redirect('variant_management')

        # ---------------- SIZE VALIDATIONS ---------------- #

        allowed_sizes = [
            'XS',
            'S',
            'M',
            'L',
            'XL',
            'XXL'
        ]

        if size.upper() not in allowed_sizes:
            messages.error(
                request,
                'Invalid size selected'
            )
            return redirect('variant_management')

        # ---------------- COLOR VALIDATIONS ---------------- #

        if len(color) < 3:
            messages.error(
                request,
                'Color name must contain at least 3 characters'
            )
            return redirect('variant_management')

        if len(color) > 30:
            messages.error(
                request,
                'Color name is too long'
            )
            return redirect('variant_management')

        # only alphabets and spaces
        if not re.match(r'^[A-Za-z\s]+$', color):
            messages.error(
                request,
                'Color name should contain only alphabets'
            )
            return redirect('variant_management')

        # prevent multiple spaces
        if "  " in color:
            messages.error(
                request,
                'Color name contains invalid spaces'
            )
            return redirect('variant_management')

        # ---------------- PRICE VALIDATIONS ---------------- #

        try:

            price = Decimal(price)

            if price <= 0:
                messages.error(
                    request,
                    'Price must be greater than 0'
                )
                return redirect('variant_management')

            if price > 1000000:
                messages.error(
                    request,
                    'Price is too high'
                )
                return redirect('variant_management')

        except InvalidOperation:
            messages.error(
                request,
                'Price must be a valid number'
            )
            return redirect('variant_management')

        # ---------------- STOCK VALIDATIONS ---------------- #

        try:

            stock = int(stock)

            if stock < 0:
                messages.error(
                    request,
                    'Stock cannot be negative'
                )
                return redirect('variant_management')

            if stock > 10000:
                messages.error(
                    request,
                    'Stock quantity is too high'
                )
                return redirect('variant_management')

        except ValueError:
            messages.error(
                request,
                'Stock must be a valid number'
            )
            return redirect('variant_management')

        # ---------------- IMAGE VALIDATIONS ---------------- #

        valid_images = [
            img for img in cropped_images
            if img
        ]

        # minimum image validation
        if len(valid_images) < 3:
            messages.error(
                request,
                'Minimum 3 variant images are required'
            )
            return redirect('variant_management')

       

        # duplicate image validation
        if len(valid_images) != len(set(valid_images)):
            messages.error(
                request,
                'Duplicate images are not allowed'
            )
            return redirect('variant_management')

        # ---------------- DUPLICATE VARIANT VALIDATION ---------------- #

        if ProductVariant.objects.filter(
            product=product,
            size__iexact=size,
            color__iexact=color,
            is_deleted=False
        ).exists():

            messages.error(
                request,
                f'Variant {size}/{color} already exists'
            )

            return redirect('variant_management')

        # ---------------- CREATE VARIANT ---------------- #

        variant = ProductVariant.objects.create(
            product=product,
            size=size.upper(),
            color=color.title(),
            variant_price=price,
            variant_stock=stock
        )

        # ---------------- SAVE IMAGES ---------------- #

        for index, img_data in enumerate(valid_images):

            try:

                # validate base64 image format
                if not img_data.startswith('data:image'):
                    variant.delete()

                    messages.error(
                        request,
                        'Invalid image format'
                    )

                    return redirect('variant_management')

                image_file = decode_base64_image(
                    img_data,
                    f'variant_{variant.id}_{index + 1}'
                )

                ProductVariantImage.objects.create(
                    variant=variant,
                    image=image_file,
                    position=index + 1,
                    is_primary=True if index == 0 else False
                )

            except Exception:

                variant.delete()

                messages.error(
                    request,
                    'Failed to upload images'
                )

                return redirect('variant_management')

        # ---------------- SUCCESS MESSAGE ---------------- #

        messages.success(
            request,
            'Variant added successfully'
        )

        return redirect('variant_management')

    return redirect('variant_management')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_variant(request, variant_id):

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_deleted=False
    )

    if request.method == 'POST':

        size = request.POST.get(
            'size',
            ''
        ).strip()

        color = request.POST.get(
            'color',
            ''
        ).strip()

        price = request.POST.get(
            'variant_price',
            ''
        ).strip()

        stock = request.POST.get(
            'variant_stock',
            ''
        ).strip()

        cropped_images = [
            request.POST.get('variant_cropped_image_1'),
            request.POST.get('variant_cropped_image_2'),
            request.POST.get('variant_cropped_image_3')
        ]

        # ---------------- REQUIRED FIELD VALIDATIONS ---------------- #

        if (
            not size or
            not color or
            not price or
            not stock
        ):
            messages.error(
                request,
                'All variant details are required'
            )
            return redirect('variant_management')

        # ---------------- SIZE VALIDATIONS ---------------- #

        allowed_sizes = [
            'XS',
            'S',
            'M',
            'L',
            'XL',
            'XXL'
        ]

        if size.upper() not in allowed_sizes:
            messages.error(
                request,
                'Invalid size selected'
            )
            return redirect('variant_management')

        # ---------------- COLOR VALIDATIONS ---------------- #

        if len(color) < 3:
            messages.error(
                request,
                'Color name must contain at least 3 characters'
            )
            return redirect('variant_management')

        if len(color) > 30:
            messages.error(
                request,
                'Color name is too long'
            )
            return redirect('variant_management')

        # only alphabets and spaces
        if not re.match(r'^[A-Za-z\s]+$', color):
            messages.error(
                request,
                'Color name should contain only alphabets'
            )
            return redirect('variant_management')

        # prevent multiple spaces
        if "  " in color:
            messages.error(
                request,
                'Color name contains invalid spaces'
            )
            return redirect('variant_management')

        # ---------------- PRICE VALIDATIONS ---------------- #

        try:

            price = Decimal(price)

            if price <= 0:
                messages.error(
                    request,
                    'Price must be greater than 0'
                )
                return redirect('variant_management')

            if price > 1000000:
                messages.error(
                    request,
                    'Price is too high'
                )
                return redirect('variant_management')

        except InvalidOperation:
            messages.error(
                request,
                'Price must be a valid number'
            )
            return redirect('variant_management')

        # ---------------- STOCK VALIDATIONS ---------------- #

        try:

            stock = int(stock)

            if stock < 0:
                messages.error(
                    request,
                    'Stock cannot be negative'
                )
                return redirect('variant_management')

            if stock > 10000:
                messages.error(
                    request,
                    'Stock quantity is too high'
                )
                return redirect('variant_management')

        except ValueError:
            messages.error(
                request,
                'Stock must be a valid number'
            )
            return redirect('variant_management')

        # ---------------- DUPLICATE VARIANT VALIDATION ---------------- #

        if ProductVariant.objects.filter(
            product=variant.product,
            size__iexact=size,
            color__iexact=color,
            is_deleted=False
        ).exclude(id=variant_id).exists():

            messages.error(
                request,
                f'Variant {size}/{color} already exists'
            )

            return redirect('variant_management')

        # ---------------- IMAGE VALIDATIONS ---------------- #

        valid_images = [
            img for img in cropped_images
            if img
        ]

        # prevent duplicate images
        if len(valid_images) != len(set(valid_images)):
            messages.error(
                request,
                'Duplicate images are not allowed'
            )
            return redirect('variant_management')

        # ---------------- IMAGE VALIDATION & DECODING ---------------- #

        decoded_images = []
        for index in range(3):
            img_data = cropped_images[index]
            if not img_data:
                continue

            # validate image format
            if not img_data.startswith('data:image'):
                messages.error(
                    request,
                    'Invalid image format'
                )
                return redirect('variant_management')

            try:
                image_file = decode_base64_image(
                    img_data,
                    f'variant_{variant.id}_{index + 1}'
                )
                decoded_images.append((index, image_file))
            except Exception:
                messages.error(
                    request,
                    'Failed to process variant images'
                )
                return redirect('variant_management')

        # ---------------- UPDATE VARIANT ATOMICALLY ---------------- #

        from django.db import transaction

        try:
            with transaction.atomic():
                variant.size = size.upper()
                variant.color = color.title()
                variant.variant_price = price
                variant.variant_stock = stock
                variant.save()

                # ---------------- IMAGE UPDATE ---------------- #
                existing_images = {
                    img.position: img
                    for img in variant.images.all().order_by('position')
                }

                for index, image_file in decoded_images:
                    position = index + 1
                    if position in existing_images:
                        old_img = existing_images[position]
                        old_img.image = image_file
                        old_img.is_primary = True if index == 0 else False
                        old_img.save()
                    else:
                        ProductVariantImage.objects.create(
                            variant=variant,
                            image=image_file,
                            position=position,
                            is_primary=True if index == 0 else False
                        )

                # ---------------- CHECK MINIMUM IMAGES ---------------- #
                total_images = variant.images.filter(
                    image__isnull=False
                ).count()

                if total_images < 3:
                    # Raise exception to trigger rollback
                    raise ValueError('Variant must contain at least 3 images')

        except ValueError as val_err:
            messages.error(request, str(val_err))
            return redirect('variant_management')
        except Exception:
            messages.error(request, 'Failed to save variant changes')
            return redirect('variant_management')

        # ---------------- SUCCESS MESSAGE ---------------- #

        messages.success(
            request,
            'Variant updated successfully'
        )

        return redirect('variant_management')

    return redirect('variant_management')

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_variant(request, variant_id):
    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_deleted=False
    )

    variant.is_deleted = True
    variant.save()

    messages.success(request, 'Variant deleted successfully')
    return redirect('variant_management')


def decode_base64_image(img_data, filename):
    format_data, imgstr = img_data.split(';base64,')
    ext = format_data.split('/')[-1]

    return ContentFile(
        base64.b64decode(imgstr),
        name=f'{filename}.{ext}'
    )


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def offer_listing(request):
    search = request.GET.get('search', '')
    offers = Offer.objects.filter(is_deleted=False).order_by('-id')
    if search:
        offers = offers.filter(Q(name__icontains=search) | Q(product__product_name__icontains=search) | Q(category__category_name__icontains=search))
    
    paginator = Paginator(offers, 10)
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