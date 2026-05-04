from django.shortcuts import render
from admin_panel.productmanagement.models import Product
from admin_panel.categorymanagement.models import Category
# Create your views here.

def prodcut_page(request):

    products=Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True).order_by('-id')
    
    category=Category.objects.filter(
        is_deleted=False,
        is_active=True)
    
    context={
        'products':products,
        'category':category
    }

    return render(request,'product_page.html',context)








