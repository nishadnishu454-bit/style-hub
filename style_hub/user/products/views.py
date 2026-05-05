from django.shortcuts import render
from django.core.paginator import Paginator
from admin_panel.productmanagement.models import Product
from admin_panel.categorymanagement.models import Category


def prodcut_page(request):
    sort = request.GET.get('sort', '')

    products = Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    )

    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-id')

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )


    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)
        

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'sort': sort,
    }

    return render(request, 'product_page.html', context)