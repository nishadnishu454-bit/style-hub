from django.shortcuts import render,redirect,get_object_or_404
from django.db.models import Q
from .models import  Category
from django.core.paginator import Paginator
from django.contrib import messages
from admin_panel.productmanagement.models import Product

# Create your views here.

def category_listing(request):

    search = request.GET.get('search','')

    categories =Category.objects.filter(
        is_deleted = False
    ).order_by('-id')


    if search:
        categories = categories.filter(
            Q(category_name__icontains=search)
        )


    paginator = Paginator(categories,5)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)


    context={
        'page_obj':categories,
       'categories':categories,
       'search':search,
    }

    return render(request,'categorylisting.html',context)





def activate_category(request, id):

    category = get_object_or_404(Category, id=id, is_deleted=False)

    category.is_active = True
    category.save()

    Product.objects.filter(
        category=category,
        is_deleted=False
    ).update(is_active=True)

    messages.success(request, 'Category activated successfully')

    return redirect('category_listing')



def deactivate_category(request, id):

    category = get_object_or_404(Category, id=id, is_deleted=False)

    category.is_active = False
    category.save()

    Product.objects.filter(
        category=category,
        is_deleted=False
    ).update(is_active=False)

    messages.success(request, 'Category deactivated successfully')

    return redirect('category_listing')




def add_category(request):

    if request.method == 'POST':

        category_name = request.POST.get('category_name')
        description = request.POST.get('description')
        category_image = request.FILES.get('category_image')

        if not category_name or not description or not category_image:
            messages.error(request, 'All fields are required')
            return redirect('add_category')

        existing_category = Category.objects.filter(
            category_name__iexact=category_name
        ).first()

        if existing_category:

            
            if existing_category.is_deleted:

                existing_category.description = description
                existing_category.category_image = category_image
                existing_category.is_deleted = False
                existing_category.is_active = True

                existing_category.save()

                messages.success(request, 'Category restored successfully')

                return redirect('category_listing')

           
            messages.error(request, 'Category already exists')

            return redirect('add_category')

        Category.objects.create(
            category_name=category_name,
            description=description,
            category_image=category_image
        )

        messages.success(request, 'Category added successfully')

        return redirect('category_listing')

    return render(request, 'addcategory.html')


def edit_category(request,id):

    category=get_object_or_404(Category,id=id,is_deleted=False)

    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        description = request.POST.get('description')
        category_image = request.FILES.get('category_image')

        existing_category = Category.objects.filter(
                category_name__iexact=category_name,
                is_deleted=False
            ).exclude(id=id)

        category.category_name = category_name
        category.description = description
        if category_image:
                category.category_image = category_image

        category.save()
        messages.success(request,'Category updated successfully')
        return redirect('category_listing')
        

    context = {
        'category':category
    }


    return render(request,'editcategory.html',context)



def delete_category(request,id):
    category =get_object_or_404(Category,id=id,is_deleted=False)
    
    category.is_deleted = True
    category.is_active = False
    category.save()
    
    Product.objects.filter(category=category).update(is_deleted=True,is_active=False)
    messages.success(request,'Category AND related products deleted successfully')

    return redirect('category_listing')

