from django.shortcuts import render
from django.core.paginator import Paginator
from admin_panel.productmanagement.models import Product
from admin_panel.categorymanagement.models import Category
from django.shortcuts import render, get_object_or_404
from django.db.models import Q


def prodcut_page(request):
    sort = request.GET.get('sort', '')
    search = request.GET.get('search', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    products = Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    )

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__category_name__icontains=search)
        )

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'a_z':
        products = products.order_by('product_name')
    elif sort == 'z_a':
        products = products.order_by('-product_name')
    else:
        products = products.order_by('-id')

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'sort': sort,
        'search': search,
        'min_price': min_price,
        'max_price': max_price,
    }

    return render(request, 'product_page.html', context)




def product_detail(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    )

    related_products = Product.objects.filter(
        category=product.category,
        is_deleted=False,
        is_active=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }

    return render(request, 'product_detial.html', context)