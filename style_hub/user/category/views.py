from django.shortcuts import render
from django.core.paginator import Paginator
from admin_panel.categorymanagement.models import Category



def category_page(request):

    category = Category.objects.filter(
        is_active=True,
        is_deleted=False
    ).order_by('-id')

    paginator = Paginator(category,8) 
    page_number = request.GET.get('page')
    category = paginator.get_page(page_number)

    context = {
        'category': category,
    }

    return render(request, 'category_page.html', context)