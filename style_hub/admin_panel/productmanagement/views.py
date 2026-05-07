from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, ProductVariant, ProductImage, ProductVariantImage
from admin_panel.categorymanagement.models import Category
import base64
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required





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
    categories = Category.objects.filter(is_deleted=False, is_active=True)

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        
      
        cropped_images = [
            request.POST.get('cropped_image_1'),
            request.POST.get('cropped_image_2'),
            request.POST.get('cropped_image_3')
        ]

        if not product_name or not description or not category_id:
            messages.error(request, 'Basic details are required')
            return redirect('add_product')

     
        valid_images = [img for img in cropped_images if img]
        if len(valid_images) < 3:
            messages.error(request, 'Exactly 3 images are required')
            return redirect('add_product')

        category = get_object_or_404(Category, id=category_id, is_deleted=False, is_active=True)

        product = Product.objects.create(
            product_name=product_name,
            description=description,
            category=category,
            price=0,
            stock=0
        )

    
        for i, img_data in enumerate(valid_images):
            format, imgstr = img_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'product_{product.id}_{i}.{ext}')
            
           
            if i == 0:
                product.product_image = data
                product.save()
            
            ProductImage.objects.create(product=product, image=data, is_primary=(i==0))

        messages.success(request, 'Product added successfully')
        return redirect('product_listing')

    context = {'categories': categories}
    return render(request, 'addproduct.html', context)





@login_required(login_url='admin_login')
def variant_management(request):
    search = request.GET.get('search', '')
    products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'variants__images')
    
    if search:
        products = products.filter(product_name__icontains=search)

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'search': search,
    }
    return render(request, 'variant_management.html', context)




@login_required(login_url='admin_login')
def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=False)

    if request.method == 'POST':
        size = request.POST.get('size')
        color = request.POST.get('color')
        price = request.POST.get('variant_price')
        stock = request.POST.get('variant_stock')
        
        cropped_images = [
            request.POST.get('variant_cropped_image_1'),
            request.POST.get('variant_cropped_image_2'),
            request.POST.get('variant_cropped_image_3')
        ]

        if not all([size, color, price, stock]):
            messages.error(request, 'All variant details are required')
            return redirect('variant_management')

        valid_images = [img for img in cropped_images if img]
        if len(valid_images) < 3:
            messages.error(request, 'Minimum 3 variant images are required')
            return redirect('variant_management')

        if ProductVariant.objects.filter(product=product, size=size, color=color, is_deleted=False).exists():
            messages.error(request, f'Variant {size}/{color} already exists')
            return redirect('variant_management')

        variant = ProductVariant.objects.create(
            product=product,
            size=size,
            color=color,
            variant_price=price,
            variant_stock=stock
        )

        for i, img_data in enumerate(valid_images):
            format, imgstr = img_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'variant_{variant.id}_{i}.{ext}')
            ProductVariantImage.objects.create(variant=variant, image=data, is_primary=(i==0))

        messages.success(request, 'Variant added successfully')
        return redirect('variant_management')

    return redirect('variant_management')





@login_required(login_url='admin_login')
def edit_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id, is_deleted=False)
    
    if request.method == 'POST':
        size = request.POST.get('size')
        color = request.POST.get('color')
        price = request.POST.get('variant_price')
        stock = request.POST.get('variant_stock')

      
        if ProductVariant.objects.filter(product=variant.product, size=size, color=color, is_deleted=False).exclude(id=variant_id).exists():
            messages.error(request, f'Variant {size}/{color} already exists')
            return redirect('variant_management')

        variant.size = size
        variant.color = color
        variant.variant_price = price
        variant.variant_stock = stock
        variant.save()


        for i in range(1, 4):
            img_data = request.POST.get(f'variant_cropped_image_{i}')
            if img_data:
                format, imgstr = img_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'variant_{variant.id}_{i}_upd.{ext}')
                
            
        
        messages.success(request, 'Variant updated successfully')
        return redirect('variant_management')

    return redirect('variant_management')





@login_required(login_url='admin_login')
def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    variant.is_deleted = True
    variant.save()
    messages.success(request, 'Variant deleted successfully')
    return redirect('variant_management')



@login_required(login_url='admin_login')
def edit_product(request, id):
    product = get_object_or_404(Product, id=id, is_deleted=False)
    categories = Category.objects.filter(is_deleted=False, is_active=True)

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        product.category = category
        product.save()

        messages.success(request, 'Product updated successfully')
        return redirect('product_listing')

    context = {'product': product, 'categories': categories}
    return render(request, 'editproduct.html', context)





@login_required(login_url='admin_login')
def view_product(request, id):
    product = get_object_or_404(Product, id=id, is_deleted=False)
    return render(request, 'viewproduct.html', {'product': product})




@login_required(login_url='admin_login')
def activate_product(request, id):

    product = get_object_or_404(Product, id=id, is_deleted=False)
    product.is_active = True

    product.save()
    messages.success(request, 'Product activated successfully')
    return redirect('view_product', id=product.id)




@login_required(login_url='admin_login')
def deactivate_product(request, id):
    product = get_object_or_404(Product, id=id, is_deleted=False)

    product.is_active = False
    product.save()
    messages.success(request, 'Product deactivated successfully')
    return redirect('view_product', id=product.id)



@login_required(login_url='admin_login')
def delete_product(request, id):
    product = get_object_or_404(Product, id=id, is_deleted=False)
    product.is_deleted = True
    product.save()
    messages.success(request, 'Product deleted successfully')
    return redirect('product_listing')