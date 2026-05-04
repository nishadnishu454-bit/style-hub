from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product
from admin_panel.categorymanagement.models import Category


def product_listing(request):

    search = request.GET.get('search', '')
    sort = request.GET.get('sort', '')

    products = Product.objects.filter(
        is_deleted=False
    ).select_related('category').order_by('-id')

    # Search
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

    # Pagination
    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'search': search,
        'sort': sort,
    }

    return render(request, 'productlisting.html', context)


def add_product(request):
    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        product_image = request.FILES.get('product_image')
        price = request.POST.get('price')
        stock = request.POST.get('stock')

        if not product_name or not description or not category_id or not product_image or not price or not stock:
            messages.error(request, 'All fields are required')
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
            product_image=product_image,
            price=price,
            stock=stock
        )

        messages.success(request, 'Product added successfully')
        return redirect('product_listing')

    context = {
        'categories': categories
    }

    return render(request, 'addproduct.html', context)



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
        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')

        category_id = request.POST.get('category')
        category = get_object_or_404(
            Category,
            id=category_id,
            is_deleted=False,
            is_active=True
        )
        product.category = category

        product_image = request.FILES.get('product_image')
        if product_image:
            product.product_image = product_image

        product.save()

        messages.success(request, 'Product updated successfully')
        return redirect('product_listing')

    context = {
        'product': product,
        'categories': categories,
    }

    return render(request, 'editproduct.html', context)



def view_product(request, id):

    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False
    )


    context = {
        'product': product,
        
    }

    return render(request, 'viewproduct.html', context)




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