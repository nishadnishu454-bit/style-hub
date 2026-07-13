from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
# Create your views here.

def admin_login(request):


    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.user.is_authenticated and not request.user.is_staff:
        messages.error(request, 'Normal users cannot access admin panel')
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request,'All fields are required')
            return render(request,'adminauth/admin_login.html')
            
        user=authenticate(request,username=username,password=password)


        if user is None:
            messages.error(request,'Invalid username or password')
            return render(request,'adminauth/admin_login.html')
        
        if not user.is_staff:
            messages.error(request,'You are not allowed to access admin panel')
            return render(request,'adminauth/admin_login.html')
        
        login(request, user)
        messages.success(request, 'Admin login successful')
        return redirect('admin_dashboard')

        
    return render(request,'adminauth/admin_login.html')



def admin_forgottpassword(request):

    return render(request,'adminauth/admin_forgottpassword.html')


def admin_emailverification(request):
    return render(request,'admin_emailverification.html')


def admin_resetpassword(request):
    return render(request,'adminauth/admin_resetpassword.html')


def admin_logout(request):
    logout(request)
    messages.success(request,'Admin logged out Successfully')
    return redirect('admin_login')



