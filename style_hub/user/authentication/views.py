from django.shortcuts import render, redirect
from django.contrib import messages
from .models import OTP,Referral
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
from .utils import send_branded_otp_email
import re
from user.wallet.utils import credit_wallet
from django.contrib.auth import get_user_model
User = get_user_model()



def login_page(request):

    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':

        old_data = request.POST
        username_or_email = request.POST.get('username_or_email','').strip()
        password = request.POST.get('password','').strip()

        context = {'old_data': old_data}

        if not username_or_email or not password:
            messages.error( request, 'All fields are required' )
            return render( request, 'authentication/login.html',context)

        if len(username_or_email) < 3:
            messages.error(request,'Username or email is too short')
            return render(request,'authentication/login.html',context)

        if len(username_or_email) > 100:
            messages.error(request, 'Username or email is too long')
            return render( request,'authentication/login.html', context)

        if len(password) < 6:
            messages.error(request,'Password must contain at least 6 characters')
            return render(request,'authentication/login.html',context )

        if len(password) > 128:
            messages.error(request, 'Password is too long')
            return render(request,'authentication/login.html',context)

        if username_or_email != username_or_email.strip():
            messages.error( request,'Invalid username or email')
            return render(request,'authentication/login.html',context )


        user = None

        if '@' in username_or_email:

            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',username_or_email):
                messages.error(request,'Invalid email format')
                return render(request,'authentication/login.html',context)
            

            user_object = User.objects.filter(email__iexact=username_or_email).first()

            if user_object:
                user = authenticate(request,username=user_object.username,password=password)

        else:

            if not re.match(r'^[A-Za-z0-9_]+$', username_or_email):
                messages.error( request, 'Username should contain only letters, numbers and underscore' )
                return render(request,'authentication/login.html',context)

            user = authenticate( request, username=username_or_email,password=password)


        if user is None:
            messages.error(request, 'Invalid credentials')
            return render(request, 'authentication/login.html', context )


        if user.is_staff or user.is_superuser:
            messages.error(request,'Admin cannot login from user side')
            return render(request,'authentication/login.html', context)


        if not user.is_email_verified:
            messages.error( request,'Please verify your email first')
            request.session['verification_user_id'] = user.id
            return redirect('email_verification')


        if not user.is_active:
            messages.error(request,'Your account is blocked')
            return render(request,'authentication/login.html', context)

        login(request, user)
        messages.success( request, 'Login successful' )
        return redirect('home')
    
    return render(request,'authentication/login.html')



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



        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'

        if not re.match(email_pattern, email):
            messages.error(request, 'Enter a valid email address')
            return render(request, 'authentication/signup.html', context)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'authentication/signup.html', context)

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
        return redirect('email_verification')
    
    context = {
        'old_data': old_data,
        'referral_code': referral_code
    }

    return render(request, 'authentication/signup.html',context)


def email_verification(request):

    user_id = request.session.get(
        'verification_user_id'
    )


    if not user_id:
        messages.error( request,'Session expired. Please signup again.')
        return redirect('signup')


    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:
        messages.error( request,'User not found')
        return redirect('signup')


    if user.is_email_verified:
        messages.info(request,'Email already verified. Please login.')
        return redirect('login')


    if request.method == 'POST':

        otp = (
            request.POST.get('otp1', '').strip() +
            request.POST.get('otp2', '').strip() +
            request.POST.get('otp3', '').strip() +
            request.POST.get('otp4', '').strip() +
            request.POST.get('otp5', '').strip() +
            request.POST.get('otp6', '').strip()
        )


        if not otp:
            messages.error( request,'Please enter OTP')
            return redirect('email_verification')


        if len(otp) != 6:
            messages.error(request,'OTP must contain exactly 6 digits')
            return redirect('email_verification')


        if not otp.isdigit():
            messages.error(request,'OTP must contain only digits')
            return redirect('email_verification')

        # ---------------- GET LATEST OTP ---------------- #

        otp_obj = OTP.objects.filter(
            user=user,
            purpose='signup_verification'
        ).order_by('-created_at').first()


        if not otp_obj:
            messages.error(request,'OTP not found. Please resend OTP.')
            return redirect('email_verification')

        # ---------------- OTP EXPIRY CHECK ---------------- #

        if otp_obj.is_expired():
            otp_obj.delete()

            messages.error(request,'OTP expired. Please resend OTP.')
            return redirect('email_verification')


        if otp_obj.code != otp:
            otp_obj.attempts += 1
            otp_obj.save()
            

            if otp_obj.attempts >= 5:
                otp_obj.delete()

                messages.error( request, 'Too many invalid attempts. Please resend OTP.')
                return redirect('email_verification')


            remaining_attempts = 5 - otp_obj.attempts
            messages.error(request,f'Invalid OTP. {remaining_attempts} attempts remaining.' )
            return redirect('email_verification')

        # ---------------- OTP VERIFIED SUCCESSFULLY ---------------- #

        user.is_email_verified = True
        user.save()

        if 'otp_failed_attempts' in request.session:
            del request.session['otp_failed_attempts']


        if user.referred_by:

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
                credit_wallet(user,50.00,'Referral Signup Benefit')
                messages.success(request, 'You received ₹50 referral signup bonus in your wallet!')

        otp_obj.delete()

        # ---------------- CLEAR SESSION DATA ---------------- #

        request.session.pop('verification_user_id',None)
        request.session.pop('referral_code',None)
        request.session.pop('otp_failed_attempts', None)


        login( request,user,backend='django.contrib.auth.backends.ModelBackend')

        messages.success( request,'Email verified successfully')
        return redirect('home')

    return render(request,'authentication/email_verification.html')


def resend_signup_otp(request):
    if request.method == "POST":

        user_id = request.session.get('verification_user_id')

        if not user_id:
            return JsonResponse({'success': False, 'message': 'Session expired'},status=401)

        user = User.objects.get(id=user_id)

        
        last_otp = OTP.objects.filter(
            user=user,
            purpose='signup_verification'
        ).order_by('-created_at').first()

        if last_otp:
            if timezone.now() < last_otp.created_at + timedelta(seconds=30):
                return JsonResponse({
                    'success': False,
                    'message': 'Please wait 30 seconds before resending OTP'
                },status=400)

       
        OTP.objects.filter(
            user=user,
            purpose='signup_verification'
        ).delete()

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
            code=otp,
            purpose='signup_verification'
        )

        send_branded_otp_email(
            email=user.email,
            otp=otp,
            purpose_text="Email Verification"
        )

        return JsonResponse({'success': True, 'message': 'New OTP sent successfully' },status=200)


def forgott_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        
        if not email:
            messages.error(request, 'Email is required')
            return redirect('auth_forgott_password')


        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(email_pattern, email):
            messages.error(request, 'Enter a valid email address')
            return redirect('auth_forgott_password')


        if len(email) > 254:
            messages.error(request, 'Email address is too long')
            return redirect('auth_forgott_password')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email')
            return redirect('auth_forgott_password')

    
        if not user.is_active:
            messages.error(request, 'This account has been blocked')
            return redirect('auth_forgott_password')

        
        if not user.is_email_verified:
            messages.error(request, 'Please verify your email before resetting password')
            return redirect('auth_forgott_password')

    
        last_otp = OTP.objects.filter(
            user=user,
            purpose='password_reset'
        ).order_by('-created_at').first()

        if last_otp:
            if timezone.now() < last_otp.created_at + timedelta(seconds=30):
                messages.error(
                    request,
                    'Please wait 30 seconds before requesting another OTP'
                )
                return redirect('auth_forgott_password')

        
        OTP.objects.filter(
            user=user,
            purpose='password_reset'
        ).delete()

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
            code=otp,
            purpose='password_reset'
        )

        try:
            send_branded_otp_email(
                email=user.email,
                otp=otp,
                purpose_text="Password Reset"
            )
        except Exception:
            messages.error(
                request,
                'Failed to send OTP. Please try again later.'
            )
            return redirect('auth_forgott_password')

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
            messages.error(request, 'OTP not found. Please request again.')
            return redirect('auth_forgott_password')


        if otp_obj.is_expired():

            otp_obj.delete()

            messages.error(request, 'OTP expired')
            return redirect('auth_forgott_password')
        


        if otp_obj.code != otp:

            otp_obj.attempts += 1
            otp_obj.save()

            if otp_obj.attempts >= 5:
                otp_obj.delete()

                messages.error(request,'Too many invalid attempts. Please request a new OTP.')
                return redirect('auth_verify_changed_password')

            remaining = 5 - otp_obj.attempts
            messages.error(request,f'Invalid OTP. {remaining} attempts remaining.')
            return redirect('auth_verify_changed_password')
    

        otp_obj.delete()

        request.session['otp_verified'] = True
        request.session['otp_verified_at'] = timezone.now().timestamp()

        messages.success(
            request,
            'OTP verified successfully'
        )
        return redirect('auth_reset_password')


    return render(request, 'authentication/verify_changed_password.html')



def reset_password(request):
    user_id = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified')
    otp_verified_at = request.session.get('otp_verified_at')

    if not user_id or not otp_verified:
        messages.error(request, 'Unauthorized access')
        return redirect('auth_forgott_password')

    # OTP verification session expires after 5 minutes
    if otp_verified_at:
        if timezone.now().timestamp() - otp_verified_at > 300:
            request.session.flush()
            messages.error(request, 'Password reset session expired')
            return redirect('auth_forgott_password')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('auth_forgott_password')

    if request.method == 'POST':

        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        
        if not password or not confirm_password:
            messages.error(request, 'All fields are required')
            return redirect('auth_reset_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('auth_reset_password')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('auth_reset_password')
        
        if len(password) > 128:
            messages.error(request, 'Password is too long')
            return redirect('auth_reset_password')

        if not re.search(r'[A-Z]', password):
            messages.error(request,'Password must contain at least one uppercase letter')
            return redirect('auth_reset_password')
        
        if not re.search(r'[a-z]', password):
            messages.error(request,'Password must contain at least one lowercase letter')
            return redirect('auth_reset_password')

        if not re.search(r'\d', password):
            messages.error(request,'Password must contain at least one number')
            return redirect('auth_reset_password')

        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request,'Password must contain at least one special character' )
            return redirect('auth_reset_password')

        if ' ' in password:
            messages.error(request,'Password cannot contain spaces')
            return redirect('auth_reset_password')

        if user.username.lower() in password.lower():
            messages.error(request,'Password should not contain your username')
            return redirect('auth_reset_password')

    
        email_name = user.email.split('@')[0].lower()

        if email_name in password.lower():
            messages.error( request, 'Password should not contain your email name')
            return redirect('auth_reset_password')

        if user.check_password(password):
            messages.error(request,'New password cannot be the same as your current password')
            return redirect('auth_reset_password')

    
        common_passwords = [
            'password',
            'password123',
            'admin123',
            '12345678',
            'qwerty123',
            'welcome123',
            'password@123',
            'admin@123'
        ]

        if password.lower() in common_passwords:
            messages.error(request,'Choose a stronger password')
            return redirect('auth_reset_password')

        user.set_password(password)
        user.save()

        # Clear session
        request.session.pop('reset_user_id', None)
        request.session.pop('otp_verified', None)
        request.session.pop('otp_verified_at', None)

        logout(request)
        messages.success(request,'Password successfully updated. Please login.')
        return redirect('login')

    return render(request, 'authentication/reset_password.html')


def resend_password_reset_otp(request):
    if request.method != "POST":
        return JsonResponse({'success': False}, status=400)

    user_id = request.session.get('reset_user_id')

    if not user_id:
        return JsonResponse({'success': False, 'message': 'Session expired'},status=401)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'},status=404)

    
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

    return JsonResponse({'success': True,'message': 'OTP resent successfully'},status=200)

def logout_user(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')