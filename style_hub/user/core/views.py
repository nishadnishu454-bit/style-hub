from django.shortcuts import render
from admin_panel.categorymanagement.models import Category

# Create your views here.
def home_page(request):
    categories = Category.objects.filter(is_active=True, is_deleted=False)
    category_map = {}
    for cat in categories:
        name = cat.category_name.lower().strip()
        category_map[name] = cat.id
        if 't-' in name or 'tshirt' in name:
            category_map['t_shirts'] = cat.id
            category_map['tshirts'] = cat.id
        elif 'shirt' in name:
            category_map['shirts'] = cat.id
        elif 'pant' in name or 'jeans' in name:
            category_map['pants'] = cat.id
            category_map['jeans'] = cat.id
        elif 'jersey' in name:
            category_map['jerseys'] = cat.id
        elif 'hoodie' in name:
            category_map['hoodies'] = cat.id
    return render(request, 'home.html', {'category_map': category_map})

def about_page(request):
    return render(request,'about.html')