from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile

import base64

from .models import Product, ProductVariant, ProductVariantImage, Offer
from admin_panel.categorymanagement.models import Category


@login_required(login_url='admin_login')
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
def add_product(request):
    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        if not product_name or not description or not category_id:
            messages.error(request, 'All fields are required')
            return redirect('add_product')

        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False
        ).exists():
            messages.error(request, 'Product already exists')
            return redirect('add_product')

        category = get_object_or_404(
            Category,
            id=category_id,
            is_deleted=False,
            is_active=True
        )

        Product.objects.create(
            product_name=product_name,
            description=description,
            category=category,
        )

        messages.success(request, 'Product added successfully')
        return redirect('product_listing')

    context = {
        'categories': categories
    }

    return render(request, 'addproduct.html', context)


@login_required(login_url='admin_login')
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
        product_name = request.POST.get('product_name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        if not product_name or not description or not category_id:
            messages.error(request, 'All fields are required')
            return redirect('edit_product', id=id)

        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False
        ).exclude(id=id).exists():
            messages.error(request, 'Product already exists')
            return redirect('edit_product', id=id)

        category = get_object_or_404(
            Category,
            id=category_id,
            is_deleted=False,
            is_active=True
        )

        product.product_name = product_name
        product.description = description
        product.category = category
        product.save()

        messages.success(request, 'Product updated successfully')
        return redirect('product_listing')

    context = {
        'product': product,
        'categories': categories,
    }

    return render(request, 'editproduct.html', context)


@login_required(login_url='admin_login')
def view_product(request, id):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'variants',
            'variants__images'
        ),
        id=id,
        is_deleted=False
    )

    context = {
        'product': product
    }

    return render(request, 'viewproduct.html', context)


@login_required(login_url='admin_login')
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
def add_variant(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_deleted=False
    )

    if request.method == 'POST':
        size = request.POST.get('size', '').strip()
        color = request.POST.get('color', '').strip()
        price = request.POST.get('variant_price')
        stock = request.POST.get('variant_stock')

        cropped_images = [
            request.POST.get('variant_cropped_image_1'),
            request.POST.get('variant_cropped_image_2'),
            request.POST.get('variant_cropped_image_3')
        ]

        if not size or not color or not price or not stock:
            messages.error(request, 'All variant details are required')
            return redirect('variant_management')

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            messages.error(request, 'Price and stock must be valid numbers')
            return redirect('variant_management')

        if price <= 0:
            messages.error(request, 'Price must be greater than 0')
            return redirect('variant_management')

        if stock < 0:
            messages.error(request, 'Stock cannot be negative')
            return redirect('variant_management')

        valid_images = [img for img in cropped_images if img]

        if len(valid_images) < 3:
            messages.error(request, 'Minimum 3 variant images are required')
            return redirect('variant_management')

        if ProductVariant.objects.filter(
            product=product,
            size__iexact=size,
            color__iexact=color,
            is_deleted=False
        ).exists():
            messages.error(request, f'Variant {size}/{color} already exists')
            return redirect('variant_management')

        variant = ProductVariant.objects.create(
            product=product,
            size=size,
            color=color,
            variant_price=price,
            variant_stock=stock
        )

        for index, img_data in enumerate(valid_images):
            try:
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
                messages.error(request, 'Invalid image format')
                return redirect('variant_management')

        messages.success(request, 'Variant added successfully')
        return redirect('variant_management')

    return redirect('variant_management')


@login_required(login_url='admin_login')
def edit_variant(request, variant_id):

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_deleted=False
    )

    if request.method == 'POST':

        size = request.POST.get('size', '').strip()
        color = request.POST.get('color', '').strip()
        price = request.POST.get('variant_price')
        stock = request.POST.get('variant_stock')

        cropped_images = [
            request.POST.get('variant_cropped_image_1'),
            request.POST.get('variant_cropped_image_2'),
            request.POST.get('variant_cropped_image_3')
        ]

        # VALIDATION
        if not size or not color or not price or not stock:
            messages.error(request, 'All variant details are required')
            return redirect('variant_management')

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            messages.error(request, 'Price and stock must be valid numbers')
            return redirect('variant_management')

        if price <= 0:
            messages.error(request, 'Price must be greater than 0')
            return redirect('variant_management')

        if stock < 0:
            messages.error(request, 'Stock cannot be negative')
            return redirect('variant_management')

        # DUPLICATE CHECK
        if ProductVariant.objects.filter(
            product=variant.product,
            size__iexact=size,
            color__iexact=color,
            is_deleted=False
        ).exclude(id=variant_id).exists():
            messages.error(request, f'Variant {size}/{color} already exists')
            return redirect('variant_management')

        # UPDATE BASIC FIELDS
        variant.size = size
        variant.color = color
        variant.variant_price = price
        variant.variant_stock = stock
        variant.save()

        # IMAGE UPDATE (IMPORTANT FIX)
        existing_images = {
                img.position: img
                for img in variant.images.all().order_by('position')
            }

        for index in range(3):
            img_data = cropped_images[index]
            if not img_data:
                continue

            try:
                image_file = decode_base64_image(
                    img_data,
                    f'variant_{variant.id}_{index + 1}'
                )

                position = index + 1

                if position in existing_images:
                    old_img = existing_images[position]
                    old_img.image = image_file
                    old_img.save()
                else:
                    ProductVariantImage.objects.create(
                        variant=variant,
                        image=image_file,
                        position=index + 1,
                        is_primary=True if index == 0 else False
                    )

            except Exception:
                messages.error(request, 'Invalid image format')
                return redirect('variant_management')

        messages.success(request, 'Variant updated successfully')
        return redirect('variant_management')

    return redirect('variant_management')

@login_required(login_url='admin_login')
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
def add_offer(request):
    products = Product.objects.filter(is_deleted=False, is_active=True)
    categories = Category.objects.filter(is_deleted=False, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        discount_type = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        offer_target = request.POST.get('offer_target', '').strip() # 'product' or 'category'
        product_id = request.POST.get('product')
        category_id = request.POST.get('category')
        
        if not name or not discount_type or not discount_value or not start_date or not end_date:
            messages.error(request, 'All fields are required')
            return redirect('add_offer')
            
        try:
            from decimal import Decimal
            discount_value = Decimal(discount_value)
            if discount_value <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return redirect('add_offer')
            if discount_type == 'PERCENTAGE' and discount_value > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return redirect('add_offer')
        except ValueError:
            messages.error(request, 'Invalid discount value')
            return redirect('add_offer')
            
        from datetime import datetime
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return redirect('add_offer')
        except ValueError:
            messages.error(request, 'Invalid dates format (should be YYYY-MM-DD)')
            return redirect('add_offer')
            
        prod = None
        cat = None
        if offer_target == 'product' and product_id:
            prod = get_object_or_404(Product, id=product_id, is_deleted=False)
        elif offer_target == 'category' and category_id:
            cat = get_object_or_404(Category, id=category_id, is_deleted=False)
        else:
            messages.error(request, 'Please select a product or category for the offer')
            return redirect('add_offer')
            
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
        messages.success(request, 'Offer created successfully')
        return redirect('offer_listing')
        
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'add_offer.html', context)


@login_required(login_url='admin_login')
def edit_offer(request, id):
    offer = get_object_or_404(Offer, id=id, is_deleted=False)
    products = Product.objects.filter(is_deleted=False, is_active=True)
    categories = Category.objects.filter(is_deleted=False, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        discount_type = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        offer_target = request.POST.get('offer_target', '').strip()
        product_id = request.POST.get('product')
        category_id = request.POST.get('category')
        
        if not name or not discount_type or not discount_value or not start_date or not end_date:
            messages.error(request, 'All fields are required')
            return redirect('edit_offer', id=id)
            
        try:
            from decimal import Decimal
            discount_value = Decimal(discount_value)
            if discount_value <= 0:
                messages.error(request, 'Discount value must be greater than 0')
                return redirect('edit_offer', id=id)
            if discount_type == 'PERCENTAGE' and discount_value > 100:
                messages.error(request, 'Percentage discount cannot exceed 100%')
                return redirect('edit_offer', id=id)
        except ValueError:
            messages.error(request, 'Invalid discount value')
            return redirect('edit_offer', id=id)
            
        from datetime import datetime
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if e_date <= s_date:
                messages.error(request, 'End date must be after start date')
                return redirect('edit_offer', id=id)
        except ValueError:
            messages.error(request, 'Invalid dates format (should be YYYY-MM-DD)')
            return redirect('edit_offer', id=id)
            
        prod = None
        cat = None
        if offer_target == 'product' and product_id:
            prod = get_object_or_404(Product, id=product_id, is_deleted=False)
        elif offer_target == 'category' and category_id:
            cat = get_object_or_404(Category, id=category_id, is_deleted=False)
        else:
            messages.error(request, 'Please select a product or category for the offer')
            return redirect('edit_offer', id=id)
            
        offer.name = name
        offer.discount_type = discount_type
        offer.discount_value = discount_value
        offer.start_date = s_date
        offer.end_date = e_date
        offer.product = prod
        offer.category = cat
        offer.save()
        
        messages.success(request, 'Offer updated successfully')
        return redirect('offer_listing')
        
    context = {
        'offer': offer,
        'products': products,
        'categories': categories,
    }
    return render(request, 'edit_offer.html', context)


@login_required(login_url='admin_login')
def delete_offer(request, id):
    offer = get_object_or_404(Offer, id=id, is_deleted=False)
    offer.is_deleted = True
    offer.save()
    messages.success(request, 'Offer deleted successfully')
    return redirect('offer_listing')


@login_required(login_url='admin_login')
def toggle_offer_status(request, id):
    offer = get_object_or_404(Offer, id=id, is_deleted=False)
    offer.is_active = not offer.is_active
    offer.save()
    messages.success(request, f'Offer status changed to {"Active" if offer.is_active else "Inactive"}')
    return redirect('offer_listing')