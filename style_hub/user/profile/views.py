from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from user.authentication.models import CustomUser as User, OTP
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
import base64
import uuid
import random
import re
from django.http import JsonResponse

@login_required(login_url='login')
def profile_page(request):
    return render(request, 'profile.html')


@login_required(login_url='login')
def editprofile_page(request):
    user = request.user

    if request.method == 'POST':
        username = request.POST.get('username')
        new_email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        cropped_image = request.POST.get('cropped_image')

        if not username or not new_email or not phone_number:
            messages.error(request, 'All fields are required')
            return redirect('editprofile')

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already taken")
            return redirect('editprofile')

        if User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
            messages.error(request, 'Email already exists')
            return redirect('editprofile')

        old_email = user.email

        user.username = username
        user.phone_number = phone_number

        if cropped_image:
            format_data, imgstr = cropped_image.split(';base64,')
            ext = format_data.split('/')[-1]
            file_name = f"{uuid.uuid4()}.{ext}"

            user.profile_photo.save(
                file_name,
                ContentFile(base64.b64decode(imgstr)),
                save=False
            )

        if new_email != old_email:
            user.save()

            request.session['pending_new_email'] = new_email
            request.session['email_change_user_id'] = user.id

            OTP.objects.filter(user=user, purpose='email_change').delete()

            otp = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=otp, purpose='email_change')

            send_mail(
                    'STYLE-HUB | Email Change Verification',
                    
                    f'''
                Hello,

                We received a request to change the email address associated with your STYLE-HUB account.

                Your OTP for email verification is:

                {otp}

                This OTP is valid for 5 minutes.

                If you did not request this change, please ignore this email and secure your account immediately.

                Thank you,
                STYLE-HUB Team
                    ''',

                    settings.EMAIL_HOST_USER,
                    [new_email],
                    fail_silently=False,
                )

            messages.success(request, 'OTP sent to your new email')
            return redirect('verify_changed_email')

        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    return render(request, 'editprofile.html')


@login_required(login_url='login')
def verify_changed_email(request):
    user_id = request.session.get('email_change_user_id')
    pending_new_email = request.session.get('pending_new_email')

    if not user_id or not pending_new_email:
        messages.error(request, 'Session expired')
        return redirect('editprofile')

    user = request.user

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
            purpose='email_change'
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, 'OTP not found')
            return redirect('verify_changed_email')

        if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
            messages.error(request, 'OTP expired')
            return redirect('editprofile')

        if otp_obj.code == otp:
            user.email = pending_new_email
            user.save()

            otp_obj.delete()
            if 'email_change_user_id' in request.session:
                del request.session['email_change_user_id']
            if 'pending_new_email' in request.session:
                del request.session['pending_new_email']

            messages.success(request, 'Email updated successfully')
            return redirect('profile')

        messages.error(request, 'Invalid OTP')
        return redirect('verify_changed_email')

    return render(request, 'verify_changed_email.html')



@login_required(login_url='login')
def resend_email_change_otp(request):

    user = request.user

    pending_new_email = request.session.get('pending_new_email')

    if not pending_new_email:
        return JsonResponse({
            'success': False,
            'message': 'Session expired'
        }, status=400)

    # delete old otp
    OTP.objects.filter(
        user=user,
        purpose='email_change'
    ).delete()

    # create new otp
    otp = str(random.randint(100000, 999999))

    OTP.objects.create(
        user=user,
        code=otp,
        purpose='email_change'
    )

    # send mail
    send_mail(
        'STYLE-HUB | Secure Email Verification',

        f'''

        STYLE-HUB


Your new OTP is:

{otp}

This OTP is valid for 5 minutes.


STYLE-HUB Team

        ''',

        settings.EMAIL_HOST_USER,
        [pending_new_email],
        fail_silently=False,
    )

    return JsonResponse({
        'success': True,
        'message': 'New OTP sent successfully'
    })





@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            messages.error(request, 'All fields are required')
            return redirect('changepassword')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('changepassword')

        if new_password != confirm_password:
            messages.error(request, 'New password do not match')
            return redirect('changepassword')
        

        if not re.match(r'^[A-Za-z0-9@]+$', new_password):
            messages.error(request, 'Password can contain only letters, numbers and @')
            return redirect('changepassword')


        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return redirect('changepassword')
        
        

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Password updated successfully')
        return redirect('profile')

    return render(request, 'changepassword.html')

