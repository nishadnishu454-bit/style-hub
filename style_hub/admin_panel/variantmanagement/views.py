from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
import base64
from decimal import Decimal, InvalidOperation
from django.db import transaction
import re
from admin_panel.productmanagement.models import Product
from admin_panel.variantmanagement.models import ProductVariant,ProductVariantImage

def is_admin(user):
    return user.is_authenticated and user.is_staff

# Create your views here.



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

    add_form_data = request.session.pop('add_variant_form_data', None)
    edit_form_data = request.session.pop('edit_variant_form_data', None)

    context = {
        'products': products,
        'search': search,
        'add_form_data': add_form_data,
        'edit_form_data': edit_form_data,
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
        
        request.session['add_variant_form_data'] = {
            'size': size,
            'color': color,
            'variant_price': price,
            'variant_stock': stock,
        }

        # ---------------- SIZE VALIDATIONS ---------------- #



        if product.category.category_name.lower()in ['pant','pants', 'jeans', 'trouser']:

            allowed_sizes = [
                '26','28','30','32','34','36',
                '38','40','42','44','46'
            ]

            final_size = size

        else:

            allowed_sizes = [
                'XS',
                'S',
                'M',
                'L',
                'XL',
                'XXL'
            ]

            final_size = size.upper()

        if final_size not in allowed_sizes:
            messages.error(
                request,
                'Invalid size selected'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # ---------------- COLOR VALIDATIONS ---------------- #

        if len(color) < 3:
            messages.error(
                request,
                'Color name must contain at least 3 characters'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        if len(color) > 30:
            messages.error(
                request,
                'Color name is too long'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # only alphabets and spaces
        if not re.match(r'^[A-Za-z\s]+$', color):
            messages.error(
                request,
                'Color name should contain only alphabets'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # prevent multiple spaces
        if "  " in color:
            messages.error(
                request,
                'Color name contains invalid spaces'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # ---------------- PRICE VALIDATIONS ---------------- #

        try:

            price = Decimal(price)

            if price <= 0:
                messages.error(
                    request,
                    'Price must be greater than 0'
                )
                return redirect(f'/variant_management/?add_variant_error={product.id}')

            if price > 1000000:
                messages.error(
                    request,
                    'Price is too high'
                )
                return redirect(f'/variant_management/?add_variant_error={product.id}')

        except InvalidOperation:
            messages.error(
                request,
                'Price must be a valid number'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # ---------------- STOCK VALIDATIONS ---------------- #

        try:

            stock = int(stock)

            if stock < 0:
                messages.error(
                    request,
                    'Stock cannot be negative'
                )
                return redirect(f'/variant_management/?add_variant_error={product.id}')

            if stock > 10000:
                messages.error(
                    request,
                    'Stock quantity is too high'
                )
                return redirect(f'/variant_management/?add_variant_error={product.id}')

        except ValueError:
            messages.error(
                request,
                'Stock must be a valid number'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

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
            return redirect(f'/variant_management/?add_variant_error={product.id}')

       

        # duplicate image validation
        if len(valid_images) != len(set(valid_images)):
            messages.error(
                request,
                'Duplicate images are not allowed'
            )
            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # ---------------- DUPLICATE VARIANT VALIDATION ---------------- #

        if ProductVariant.objects.filter(
            product=product,
            size__iexact=final_size,
            color__iexact=color,
            is_deleted=False
        ).exists():

            messages.error(
                request,
                f'Variant {size}/{color} already exists'
            )

            return redirect(f'/variant_management/?add_variant_error={product.id}')

        # ---------------- CREATE VARIANT ---------------- #

        variant = ProductVariant.objects.create(
            product=product,
            size=final_size,
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

                    return redirect(f'/variant_management/?add_variant_error={product.id}')

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

                return redirect(f'/variant_management/?add_variant_error={product.id}')

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
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')
        

        request.session['edit_variant_form_data'] = {
            'size': size,
            'color': color,
            'variant_price': price,
            'variant_stock': stock,
        }

        # ---------------- SIZE VALIDATIONS ---------------- #
        if variant.product.category.category_name.lower() in ['pant','pants', 'jeans', 'trouser']:
            allowed_sizes = [
                '26','28','30','32','34','36',
                '38','40','42','44','46'
            ]

            final_size = size

        else:
            allowed_sizes = [
                'XS',
                'S',
                'M',
                'L',
                'XL',
                'XXL'
            ]

            final_size = size.upper()

        if final_size not in allowed_sizes:
            messages.error(
                request,
                'Invalid size selected'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # ---------------- COLOR VALIDATIONS ---------------- #

        if len(color) < 3:
            messages.error(
                request,
                'Color name must contain at least 3 characters'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        if len(color) > 30:
            messages.error(
                request,
                'Color name is too long'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # only alphabets and spaces
        if not re.match(r'^[A-Za-z\s]+$', color):
            messages.error(
                request,
                'Color name should contain only alphabets'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # prevent multiple spaces
        if "  " in color:
            messages.error(
                request,
                'Color name contains invalid spaces'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # ---------------- PRICE VALIDATIONS ---------------- #

        try:

            price = Decimal(price)

            if price <= 0:
                messages.error(
                    request,
                    'Price must be greater than 0'
                )
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

            if price > 1000000:
                messages.error(
                    request,
                    'Price is too high'
                )
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        except InvalidOperation:
            messages.error(
                request,
                'Price must be a valid number'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # ---------------- STOCK VALIDATIONS ---------------- #

        try:

            stock = int(stock)

            if stock < 0:
                messages.error(
                    request,
                    'Stock cannot be negative'
                )
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

            if stock > 10000:
                messages.error(
                    request,
                    'Stock quantity is too high'
                )
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        except ValueError:
            messages.error(
                request,
                'Stock must be a valid number'
            )
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # ---------------- DUPLICATE VARIANT VALIDATION ---------------- #

        if ProductVariant.objects.filter(
            product=variant.product,
            size__iexact=final_size,
            color__iexact=color,
            is_deleted=False
        ).exclude(id=variant_id).exists():

            messages.error(
                request,
                f'Variant {size}/{color} already exists'
            )

            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

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
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

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
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

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
                return redirect(f'/variant_management/?edit_variant_error={variant.id}')

        # ---------------- UPDATE VARIANT ATOMICALLY ---------------- #

        

        try:
            with transaction.atomic():
                variant.size = final_size
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
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')
        except Exception:
            messages.error(request, 'Failed to save variant changes')
            return redirect(f'/variant_management/?edit_variant_error={variant.id}')

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
