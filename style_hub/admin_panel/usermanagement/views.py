from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def user_management(request):
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', '')

    users = User.objects.filter(is_staff=False)

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )

    if sort == 'name_asc':
        users = users.order_by('username')
    elif sort == 'name_desc':
        users = users.order_by('-username')
    elif sort == 'oldest':
        users = users.order_by('date_joined')
    else:
        users = users.order_by('-date_joined')

    paginator = Paginator(users, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'sort': sort,
        'total_users': users.count(),
    }

    return render(request, 'usermanagement/usermanagement.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def user_detail(request, user_id):
    user_obj = get_object_or_404(User, id=user_id, is_staff=False)

    context = {
        'user_obj': user_obj,
    }

    return render(request, 'usermanagement/userdetial.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def block_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id, is_staff=False)


    user_obj.is_active = False
    user_obj.save()

    messages.success(request, 'User blocked successfully')
    return redirect('user_management')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def unblock_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id, is_staff=False)

    
    user_obj.is_active = True
    user_obj.save()

    messages.success(request, 'User unblocked successfully')
    return redirect('user_management')