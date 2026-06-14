from django.shortcuts import render
from admin_panel.categorymanagement.models import Category
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied


# Create your views here.
def home_page(request):
    categories = Category.objects.filter(is_active=True, is_deleted=False)
    category_map = {}
    for cat in categories:
        name = cat.category_name.lower().strip()

        # T-Shirts
        if 't-shirt' in name or 'tshirt' in name or 't shirt' in name:
            category_map['t_shirts'] = cat.id

        # Shirts
        elif 'shirt' in name:
            category_map['shirts'] = cat.id

        # Pants / Jeans
        elif 'pant' in name or 'jean' in name:
            category_map['pants'] = cat.id

        # Jerseys
        elif 'jersey' in name or 'jersy' in name:
             category_map['jerseys'] = cat.id

        # Hoodies
        elif 'hoodie' in name or 'hoodies' in name:
            category_map['hoodies'] = cat.id
    return render(request, 'home.html', {'category_map': category_map})





def about_page(request):
    return render(request,'about.html')

