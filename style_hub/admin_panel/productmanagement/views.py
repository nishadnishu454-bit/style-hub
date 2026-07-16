from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
import re
from .models import Product
from admin_panel.categorymanagement.models import Category
from django.db.models import Sum

def is_admin(user):
    return user.is_authenticated and user.is_staff


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
        product_name = request.POST.get('product_name','').strip()
        description = request.POST.get('description','').strip()
        category_id = request.POST.get('category')

        context = {
        'categories': categories,
        'old_data':request.POST
        }


        if (
            not product_name or
            not description or
            not category_id
        ):
            messages.error(
                request,
                'All fields are required'
            )
            return render(request, 'addproduct.html', context)

        if len(product_name) < 3:
            messages.error(request,'Product name must contain at least 3 characters')
            return render(request, 'addproduct.html', context)

        if len(product_name) > 100:
            messages.error( request,'Product name is too long')
            return render(request, 'addproduct.html', context)


        if "  " in product_name:
            messages.error(request,'Product name contains invalid spaces')
            return render(request, 'addproduct.html', context)


        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', product_name):
            messages.error( request,'Product name contains invalid characters')
            return render(request, 'addproduct.html', context)


        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False).exists():

            messages.error(request,'Product already exists' )
            return render(request, 'addproduct.html', context)


        if len(description) < 10:
            messages.error(request,'Description must contain at least 10 characters')
            return render(request, 'addproduct.html', context)

        if len(description) > 2000:
            messages.error(request,'Description is too long')
            return render(request, 'addproduct.html', context)

        if description.isdigit():
            messages.error( request,'Description cannot contain only numbers')
            return render(request, 'addproduct.html', context)


        try:

            category = get_object_or_404(
                Category,
                id=category_id,
                is_deleted=False,
                is_active=True
            )

        except:

            messages.error( request,'Invalid category selected')
            return render(request, 'addproduct.html', context)


        Product.objects.create(
            product_name=product_name,
            description=description,
            category=category,
        )

        messages.success(request,'Product added successfully')
        return redirect('product_listing')
    
    context = {
    'categories': categories
    }

    return render(request,'addproduct.html',context)



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

        product_name = request.POST.get('product_name','').strip()
        description = request.POST.get('description','').strip()
        category_id = request.POST.get('category')


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



        if len(product_name) < 3:
            messages.error(
                request,
                'Product name must contain at least 3 characters'
            )
            return redirect('edit_product', id=id)


        if len(product_name) > 100:
            messages.error(
                request,
                'Product name is too long'
            )
            return redirect('edit_product', id=id)



        if "  " in product_name:
            messages.error(
                request,
                'Product name contains invalid spaces'
            )
            return redirect('edit_product', id=id)


        if not re.match(r'^[A-Za-z0-9\s\-\&]+$', product_name):
            messages.error(
                request,
                'Product name contains invalid characters'
            )
            return redirect('edit_product', id=id)


        if Product.objects.filter(
            product_name__iexact=product_name,
            is_deleted=False
        ).exclude(id=id).exists():

            messages.error(
                request,
                'Product already exists'
            )
            return redirect('edit_product', id=id)


        if len(description) < 20:
            messages.error(
                request,
                'Description must contain at least 20 characters'
            )
            return redirect('edit_product', id=id)

        if len(description) > 2000:
            messages.error(
                request,
                'Description is too long'
            )
            return redirect('edit_product', id=id)


        if description.isdigit():
            messages.error(
                request,
                'Description cannot contain only numbers'
            )
            return redirect('edit_product', id=id)

        if "  " in description:
            messages.error(
                request,
                'Description contains invalid spaces'
            )
            return redirect('edit_product', id=id)


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

    variants = product.variants.filter(is_deleted = False)

    stock_data = variants.aggregate(
    total=Sum('variant_stock')
)
    total_stock = stock_data['total'] or 0

    context = {
        'product': product,
        'total_stock':total_stock,
        'variants':variants
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




