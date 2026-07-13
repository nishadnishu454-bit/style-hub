from django.shortcuts import render,redirect,get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import  Category
from django.core.paginator import Paginator
from django.contrib import messages
from admin_panel.productmanagement.models import Product
import os
import re


# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
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



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
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



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
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



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_category(request):

    if request.method == 'POST':

        category_name = request.POST.get('category_name', '').strip()
        description = request.POST.get('description', '').strip()
        category_image = request.FILES.get('category_image')


        if not category_name:
            messages.error(request, 'Category name is required')
            return redirect('add_category')

        if not description:
            messages.error(request, 'Description is required')
            return redirect('add_category')

        if not category_image:
            messages.error(request, 'Category image is required')
            return redirect('add_category')


        if len(category_name) < 3:
            messages.error(request, 'Category name must contain at least 3 characters')
            return redirect('add_category')

        if len(category_name) > 50:
            messages.error(request, 'Category name is too long')
            return redirect('add_category')

        if not re.match(r'^[A-Za-z\s]+$', category_name):
            messages.error(request, 'Category name should contain only alphabets and spaces')
            return redirect('add_category')

        if "  " in category_name:
            messages.error(request, 'Category name contains invalid spaces')
            return redirect('add_category')

        if len(description) < 10:
            messages.error(request, 'Description must contain at least 10 characters')
            return redirect('add_category')

        if len(description) > 500:
            messages.error(request, 'Description is too long')
            return redirect('add_category')


        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']

        ext = os.path.splitext(category_image.name)[1].lower()

        if ext not in allowed_extensions:
            messages.error(
                request,
                'Only JPG, JPEG, PNG and WEBP images are allowed'
            )
            return redirect('add_category')

        if category_image.size > 5 * 1024 * 1024:
            messages.error(request, 'Image size should be less than 5MB')
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




@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_category(request, id):

    category = get_object_or_404(
        Category,
        id=id,
        is_deleted=False
    )

    if request.method == 'POST':

        category_name = request.POST.get('category_name','').strip()
        description = request.POST.get( 'description','').strip()
        category_image = request.FILES.get('category_image')


        if not category_name:
            messages.error(request,'Category name is required')
            return redirect('edit_category', id=id)

        if not description:
            messages.error(request, 'Description is required')
            return redirect('edit_category', id=id)


        if len(category_name) < 3:
            messages.error(request,'Category name must contain at least 3 characters')
            return redirect('edit_category', id=id)

        if len(category_name) > 50:
            messages.error(request,'Category name is too long' )
            return redirect('edit_category', id=id)

        if not re.match(r'^[A-Za-z\s]+$', category_name):
            messages.error( request,'Category name should contain only alphabets and spaces')
            return redirect('edit_category', id=id)

        if "  " in category_name:
            messages.error(request,'Category name contains invalid spaces' )
            return redirect('edit_category', id=id)


        if len(description) < 10:
            messages.error( request,'Description must contain at least 10 characters')
            return redirect('edit_category', id=id)

        if len(description) > 500:
            messages.error(request,'Description is too long')
            return redirect('edit_category', id=id)


        if category_image:

            allowed_extensions = [
                '.jpg',
                '.jpeg',
                '.png',
                '.webp'
            ]

            ext = os.path.splitext(
                category_image.name
            )[1].lower()

            # image extension validation
            if ext not in allowed_extensions:
                messages.error(
                    request,
                    'Only JPG, JPEG, PNG and WEBP images are allowed'
                )
                return redirect('edit_category', id=id)

            # image size validation (max 5MB)
            if category_image.size > 5 * 1024 * 1024:
                messages.error(
                    request,
                    'Image size should be less than 5MB'
                )
                return redirect('edit_category', id=id)


        existing_category = Category.objects.filter(
            category_name__iexact=category_name,
            is_deleted=False
        ).exclude(id=id)

        if existing_category.exists():
            messages.error(request,'Category name already exists')
            return redirect('edit_category', id=id)


        category.category_name = category_name
        category.description = description

        if category_image:
            category.category_image = category_image

        category.save()

        messages.success(request,'Category updated successfully')
        return redirect('category_listing')

    context = {
        'category': category
    }

    return render(request,'editcategory.html',context)



@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_category(request,id):
    category =get_object_or_404(Category,id=id,is_deleted=False)
    
    category.is_deleted = True
    category.is_active = False
    category.save()
    
    Product.objects.filter(category=category).update(is_deleted=True,is_active=False)
    messages.success(request,'Category AND related products deleted successfully')
    return redirect('category_listing')

