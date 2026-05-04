from django.shortcuts import render
from admin_panel.categorymanagement.models import Category
from admin_panel.productmanagement.models import Product


# Create your views here.


def category_page(request):

    products=Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True
    ).order_by('-id')
    
    category=Category.objects.filter(is_active=True,is_deleted=False)
    

    context={
        'category':category,
        'products':products
    }
    return render(request,'category_page.html',context)

