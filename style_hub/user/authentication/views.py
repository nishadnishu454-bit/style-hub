from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser as User, OTP
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
from .utils import send_branded_otp_email
import re
from django.contrib.auth import get_user_model

def login_page(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        old_data = request.POST
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')

        if not username_or_email or not password:
            messages.error(request, 'All fields are required')
            context={'old_data':old_data}

            return render(request, 'authentication/login.html', context)
        

        user = None

        if User.objects.filter(email__iexact=username_or_email).exists():
            user_object = User.objects.get(email__iexact=username_or_email)
            user = authenticate(request, username=user_object.username, password=password)
        else:
            user = authenticate(request, username=username_or_email, password=password)

        if user is None:
            messages.error(request, 'Invalid credentials')
            context={'old_data':old_data}
            return render(request, 'authentication/login.html', context)

        
        if user.is_staff or user.is_superuser:
            messages.error(request, 'Admin cannot login from user side')
            context={'old_data':old_data}
            return render(request, 'authentication/login.html', context)

        if not user.is_email_verified:
            messages.error(request, 'Please verify your email first')
            request.session['verification_user_id'] = user.id
            return redirect('email_verfication')
        
        
        if not user.is_active:
            messages.error(request, "Your account is blocked")
            context={'old_data':old_data}
            return render(request, 'authentication/login.html', context)
        
                

        login(request, user)
        messages.success(request, 'Login Successful')
        return redirect('home')

    return render(request, 'authentication/login.html')


User = get_user_model()

def signup_page(request):
    ref_code = request.GET.get('ref')

    if ref_code:
        request.session['referral_code'] = ref_code

    old_data = {}
    referral_code = request.session.get('referral_code', '')


    if request.method == 'POST':
        old_data = request.POST

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms = request.POST.get('terms')

        context={
            'old_data':old_data,
            'referral_code': referral_code
            }

        if not username or not email or not phone_number or not password or not confirm_password:
            messages.error(request, 'All fields are required')
            return render(request, 'authentication/signup.html', context)

        # Username validations
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters')
            return render(request, 'authentication/signup.html', context)

        if len(username) > 20:
            messages.error(request, 'Username cannot exceed 20 characters')
            return render(request, 'authentication/signup.html', context)

        if ' ' in username:
            messages.error(request, 'Username cannot contain spaces')
            return render(request, 'authentication/signup.html', context)

        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', username):
            messages.error(request, 'Username must start with a letter and can only contain letters, numbers, and underscore')
            return render(request, 'authentication/signup.html', context)

        if username.isdigit():
            messages.error(request, 'Username cannot contain only numbers')
            return render(request, 'authentication/signup.html', context)

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'authentication/signup.html', context)

        # Email validations
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'

        if not re.match(email_pattern, email):
            messages.error(request, 'Enter a valid email address')
            return render(request, 'authentication/signup.html', context)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'authentication/signup.html', context)

        # Phone validations
        if not phone_number.isdigit():
            messages.error(request, 'Phone number must contain only digits')
            return render(request, 'authentication/signup.html', context)

        if len(phone_number) != 10:
            messages.error(request, 'Phone number must be 10 digits')
            return render(request, 'authentication/signup.html', context)

        if phone_number[0] not in ['6', '7', '8', '9']:
            messages.error(request, 'Enter a valid Indian phone number')
            return render(request, 'authentication/signup.html', context)

        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone number already exists')
            return render(request, 'authentication/signup.html', context)

        # Password validations
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'authentication/signup.html', context)

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'authentication/signup.html', context)

        if not re.search(r'[A-Z]', password):
            messages.error(request, 'Password must contain at least one uppercase letter')
            return render(request, 'authentication/signup.html', context)

        if not re.search(r'[a-z]', password):
            messages.error(request, 'Password must contain at least one lowercase letter')
            return render(request, 'authentication/signup.html', context)

        if not re.search(r'\d', password):
            messages.error(request, 'Password must contain at least one number')
            return render(request, 'authentication/signup.html', context)

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, 'Password must contain at least one special character')
            return render(request, 'authentication/signup.html', context)

        if username.lower() in password.lower():
            messages.error(request, 'Password should not contain your username')
            return render(request, 'authentication/signup.html', context)

        if not terms:
            messages.error(request, "Please accept Terms and Privacy Policy")
            return render(request, 'authentication/signup.html', context)

        referred_by_user = None
        referral_code_input = request.POST.get('referral_code', '').strip().upper()
        session_ref_code = referral_code_input or request.session.get('referral_code')

        if session_ref_code:
            try:
                referred_by_user = User.objects.get(referral_code=session_ref_code)
            except User.DoesNotExist:
                if referral_code_input:
                    messages.error(request, 'Invalid referral code')
                    return render(request, 'authentication/signup.html', context)

        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password,
            is_email_verified=False,
            referred_by=referred_by_user
        )

        OTP.objects.filter(user=user, purpose='signup_verification').delete()

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
            code=otp,
            purpose='signup_verification'
        )

        send_branded_otp_email(
            email=email,
            otp=otp,
            purpose_text="Email Verification"
        )

        request.session['verification_user_id'] = user.id

        messages.success(request, 'OTP sent to your email')
        return redirect('email_verfication')
    
    context = {
        'old_data': old_data,
        'referral_code': referral_code
    }

    return render(request, 'authentication/signup.html',context)


def email_verfication(request):
    user_id = request.session.get('verification_user_id')

    if not user_id:
        messages.error(request, 'Session expired')
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signup')

    if request.method == 'POST':
        otp = (
            request.POST.get('otp1', '') +
            request.POST.get('otp2', '') +
            request.POST.get('otp3', '') +
            request.POST.get('otp4', '') +
            request.POST.get('otp5', '') +
            request.POST.get('otp6', '')
        )

        otp_obj = OTP.objects.filter(
            user=user,
            purpose='signup_verification'
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, 'OTP not found')
            return redirect('email_verfication')

        if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
            messages.error(request, 'OTP expired')
            return redirect('signup')

        if otp_obj.code == otp:
            user.is_email_verified = True
            user.save()

            if user.referred_by:
                from user.authentication.models import Referral
                from user.wallet.utils import credit_wallet
                referral, created = Referral.objects.get_or_create(
                    referred_user=user,
                    defaults={
                        'referrer': user.referred_by,
                        'benefit_amount_referred': 50.00,
                        'benefit_amount_referrer': 100.00,
                        'is_referrer_rewarded': False
                    }
                )
                if created:
                    credit_wallet(user, 50.00, 'Referral Signup Benefit')
                    messages.success(request, 'You received ₹50 referral signup bonus in your wallet!')

            otp_obj.delete()
            if 'verification_user_id' in request.session:
                del request.session['verification_user_id']
            if 'referral_code' in request.session:
                del request.session['referral_code']

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Email verified successfully')
            return redirect('home')

        messages.error(request, 'Invalid OTP')
        return redirect('email_verfication')

    return render(request, 'authentication/email_verfication.html')





def forgott_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, 'Email is required')
            return redirect('auth_forgott_password')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email')
            return redirect('auth_forgott_password')

        OTP.objects.filter(user=user, purpose='password_reset').delete()

        otp = str(random.randint(100000, 999999))
        OTP.objects.create(
            user=user,
            code=otp,
            purpose='password_reset'
        )

        send_branded_otp_email(
            email=user.email,
            otp=otp,
            purpose_text="Password Reset"
        )

        request.session['reset_user_id'] = user.id
        messages.success(request, 'OTP sent to your email')
        return redirect('auth_verify_changed_password')

    return render(request, 'authentication/forgott_password.html')



def verify_changed_password(request):
    user_id = request.session.get('reset_user_id')

    if not user_id:
        messages.error(request, 'Session expired')
        return redirect('auth_forgott_password')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('auth_forgott_password')

    if request.method == 'POST':
        otp = (
            request.POST.get('otp1', '') +
            request.POST.get('otp2', '') +
            request.POST.get('otp3', '') +
            request.POST.get('otp4', '') +
            request.POST.get('otp5', '') +
            request.POST.get('otp6', '')
        )

        otp_obj = OTP.objects.filter(
            user=user,
            purpose='password_reset'
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, 'OTP not found')
            return redirect('auth_verify_changed_password')

        if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
            messages.error(request, 'OTP expired')
            return redirect('auth_forgott_password')

        if otp_obj.code == otp:
            request.session['otp_verified'] = True
            otp_obj.delete()

            messages.success(request, 'OTP verified successfully')
            return redirect('auth_reset_password')

        messages.error(request, 'Invalid OTP')
        return redirect('auth_verify_changed_password')

    return render(request, 'authentication/verify_changed_password.html')




def resend_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=405)

    if request.session.get('verification_user_id'):
        user_id = request.session.get('verification_user_id')
        purpose = 'signup_verification'

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"}, status=404)

        email = user.email

    
    elif request.session.get('reset_user_id'):
        user_id = request.session.get('reset_user_id')
        purpose = 'password_reset'

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"}, status=404)

        email = user.email

  
    elif request.user.is_authenticated and request.session.get('new_email'):
        user = request.user
        purpose = 'email_change'
        email = request.session.get('new_email')

    else:
        return JsonResponse({"success": False, "message": "Session expired"}, status=400)

  
    OTP.objects.filter(user=user, purpose=purpose).delete()

   
    otp = str(random.randint(100000, 999999))

    OTP.objects.create(
        user=user,
        code=otp,
        purpose=purpose
    )

    send_branded_otp_email(
        email=email,
        otp=otp,
        purpose_text="OTP Verification"
    )

    return JsonResponse({"success": True, "message": "New OTP sent"})



def reset_password(request):
    user_id = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified')

    if not user_id or not otp_verified:
        messages.error(request, 'Unauthorized access')
        return redirect('auth_forgott_password')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('auth_forgott_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not password or not confirm_password:
            messages.error(request, 'All fields are required')
            return redirect('auth_reset_password')

        if password != confirm_password:
            messages.error(request, 'Password does not match')
            return redirect('auth_reset_password')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return redirect('auth_reset_password')

        user.set_password(password)
        user.save()

        if 'reset_user_id' in request.session:
            del request.session['reset_user_id']
        if 'otp_verified' in request.session:
            del request.session['otp_verified']

        logout(request)
        messages.success(request, 'Password successfully updated. Please login.')
        return redirect('login')

    return render(request, 'authentication/reset_password.html')




def logout_user(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')