from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    total_users = User.objects.filter(is_staff=False).count()
    active_users = User.objects.filter(is_staff=False, is_active=False).count()
    blocked_users = User.objects.filter(is_staff=False, is_active=True).count()

    context = {
    'total_revenue': 0,
    'total_orders': 0,
    'total_users': total_users,
    'active_users': active_users,
    'processing_orders': 0,
    'shipped_orders': 0,
    'return_orders': 0,
    'recent_orders': [],
    'sales_chart': [],
}

    return render(request, 'admindashboard/admin_dashboard.html', context)