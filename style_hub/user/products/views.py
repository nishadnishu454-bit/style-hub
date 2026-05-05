from django.shortcuts import render
from django.core.paginator import Paginator
from admin_panel.productmanagement.models import Product
from admin_panel.categorymanagement.models import Category


def prodcut_page(request):
    products = Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    ).order_by('-id')

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories
    }

    return render(request, 'product_page.html', context)