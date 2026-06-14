from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address
from django.db.models import Q
from django.urls import reverse
import re

@login_required(login_url='login')
def address_page(request):
    query = request.GET.get('q')
    address = Address.objects.filter(user=request.user)
    if query:
        address = address.filter(
            Q(full_name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(address__icontains=query) |
            Q(area__icontains=query) |
            Q(district__icontains=query) |
            Q(state__icontains=query) |
            Q(pincode__icontains=query)
        )

    return render(request, 'address.html', {'addresses': address})


@login_required(login_url='login')
def add_address_page(request):

    next_url = request.GET.get('next') or request.POST.get('next', '')

    context = {
        "next": next_url,
        "old": request.POST
    }

    if request.method == 'POST':

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        phone_number = request.POST.get(
            'phone_number',
            ''
        ).strip()

        house_name = request.POST.get(
            'house_name',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        area = request.POST.get(
            'area',
            ''
        ).strip()

        country = request.POST.get(
            'country',
            ''
        ).strip()

        district = request.POST.get(
            'district',
            ''
        ).strip()

        state = request.POST.get(
            'state',
            ''
        ).strip()

        pincode = request.POST.get(
            'pincode',
            ''
        ).strip()

        address_type = request.POST.get(
            'address_type',
            ''
        ).strip()

        is_default = request.POST.get(
            'is_default'
        ) == 'on'

        # ---------------- REQUIRED FIELD VALIDATION ---------------- #

        if not all([
            full_name,
            phone_number,
            house_name,
            address,
            area,
            country,
            district,
            state,
            pincode,
            address_type
        ]):

            messages.error(
                request,
                "All fields are required"
            )

            return render(
                request,
                'add_address.html',
                context
            )

        # ---------------- FULL NAME VALIDATION ---------------- #

        if len(full_name) < 3:
            messages.error(
                request,
                "Full name must contain at least 3 characters"
            )
            return render(request, 'add_address.html', context)

        if len(full_name) > 100:
            messages.error(
                request,
                "Full name is too long"
            )
            return render(request, 'add_address.html', context)

        if not re.match(r'^[A-Za-z\s]+$', full_name):
            messages.error(
                request,
                "Full name should contain only alphabets"
            )
            return render(request, 'add_address.html', context)

        if "  " in full_name:
            messages.error(
                request,
                "Full name contains invalid spaces"
            )
            return render(request, 'add_address.html', context)

        # ---------------- PHONE NUMBER VALIDATION ---------------- #

        if not phone_number.isdigit():
            messages.error(
                request,
                "Phone number must contain only digits"
            )
            return render(request, 'add_address.html', context)

        if len(phone_number) != 10:
            messages.error(
                request,
                "Phone number must contain exactly 10 digits"
            )
            return render(request, 'add_address.html', context)

        # Indian mobile number validation
        if not re.match(r'^[6-9]\d{9}$', phone_number):
            messages.error(
                request,
                "Invalid phone number"
            )
            return render(request, 'add_address.html', context)

        # ---------------- HOUSE NAME VALIDATION ---------------- #

        if len(house_name) < 2:
            messages.error(
                request,
                "House name must contain at least 2 characters"
            )
            return render(request, 'add_address.html', context)

        if len(house_name) > 100:
            messages.error(
                request,
                "House name is too long"
            )
            return render(request, 'add_address.html', context)

        # ---------------- ADDRESS VALIDATION ---------------- #

        if len(address) < 10:
            messages.error(
                request,
                "Address must contain at least 10 characters"
            )
            return render(request, 'add_address.html', context)

        if len(address) > 300:
            messages.error(
                request,
                "Address is too long"
            )
            return render(request, 'add_address.html', context)

        # ---------------- AREA VALIDATION ---------------- #

        if len(area) < 2:
            messages.error(
                request,
                "Area name is too short"
            )
            return render(request, 'add_address.html', context)

        if len(area) > 100:
            messages.error(
                request,
                "Area name is too long"
            )
            return render(request, 'add_address.html', context)

        # ---------------- DISTRICT VALIDATION ---------------- #

        if len(district) < 2:
            messages.error(
                request,
                "District name is too short"
            )
            return render(request, 'add_address.html', context)

        if len(district) > 100:
            messages.error(
                request,
                "District name is too long"
            )
            return render(request, 'add_address.html', context)

        if not re.match(r'^[A-Za-z\s]+$', district):
            messages.error(
                request,
                "District name should contain only alphabets"
            )
            return render(request, 'add_address.html', context)

        # ---------------- STATE VALIDATION ---------------- #

        if len(state) < 2:
            messages.error(
                request,
                "State name is too short"
            )
            return render(request, 'add_address.html', context)

        if len(state) > 100:
            messages.error(
                request,
                "State name is too long"
            )
            return render(request, 'add_address.html', context)

        if not re.match(r'^[A-Za-z\s]+$', state):
            messages.error(
                request,
                "State name should contain only alphabets"
            )
            return render(request, 'add_address.html', context)

        # ---------------- COUNTRY VALIDATION ---------------- #

        if len(country) < 2:
            messages.error(
                request,
                "Country name is too short"
            )
            return render(request, 'add_address.html', context)

        if len(country) > 100:
            messages.error(
                request,
                "Country name is too long"
            )
            return render(request, 'add_address.html', context)

        if not re.match(r'^[A-Za-z\s]+$', country):
            messages.error(
                request,
                "Country name should contain only alphabets"
            )
            return render(request, 'add_address.html', context)

        # ---------------- PINCODE VALIDATION ---------------- #

        if not pincode.isdigit():
            messages.error(
                request,
                "Pincode must contain only digits"
            )
            return render(request, 'add_address.html', context)

        if len(pincode) != 6:
            messages.error(
                request,
                "Pincode must contain exactly 6 digits"
            )
            return render(request, 'add_address.html', context)

        if pincode.startswith('0'):
            messages.error(
                request,
                "Invalid pincode"
            )
            return render(request, 'add_address.html', context)

        # ---------------- ADDRESS TYPE VALIDATION ---------------- #

        allowed_address_types = [
            'Home',
            'Office',
            'Other'
        ]

        if address_type not in allowed_address_types:
            messages.error(
                request,
                "Invalid address type selected"
            )
            return render(request, 'add_address.html', context)

        # ---------------- DUPLICATE ADDRESS VALIDATION ---------------- #

        duplicate_address = Address.objects.filter(
            user=request.user,
            full_name__iexact=full_name,
            phone_number=phone_number,
            house_name__iexact=house_name,
            address__iexact=address,
            pincode=pincode
        ).exists()

        if duplicate_address:
            messages.error(
                request,
                "This address already exists"
            )
            return render(request, 'add_address.html', context)

        # ---------------- DEFAULT ADDRESS HANDLING ---------------- #

        if is_default:

            Address.objects.filter(
                user=request.user,
                is_default=True
            ).update(is_default=False)

        # ---------------- CREATE ADDRESS ---------------- #

        Address.objects.create(
            user=request.user,
            full_name=full_name.title(),
            phone_number=phone_number,
            house_name=house_name.title(),
            address=address,
            area=area.title(),
            country=country.title(),
            district=district.title(),
            state=state.title(),
            pincode=pincode,
            address_type=address_type,
            is_default=is_default
        )

        messages.success(
            request,
            "Address added successfully"
        )

        if next_url == 'checkout':
            return redirect('checkout')

        return redirect('address_page')

    return render(
        request,
        'add_address.html',
        context
    )

@login_required(login_url='login')
def set_default_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)

    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

    address.is_default = True
    address.save()

    messages.success(request, "Default address updated")
    return redirect('address_page')


@login_required(login_url='login')
def edit_address_page(request, id):

    address_obj = get_object_or_404(
        Address,
        id=id,
        user=request.user
    )

    next_url = request.GET.get('next') or request.POST.get('next', '')

    if request.method == 'POST':

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        phone_number = request.POST.get(
            'phone_number',
            ''
        ).strip()

        house_name = request.POST.get(
            'house_name',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        area = request.POST.get(
            'area',
            ''
        ).strip()

        country = request.POST.get(
            'country',
            ''
        ).strip()

        district = request.POST.get(
            'district',
            ''
        ).strip()

        state = request.POST.get(
            'state',
            ''
        ).strip()

        pincode = request.POST.get(
            'pincode',
            ''
        ).strip()

        address_type = request.POST.get(
            'address_type',
            ''
        ).strip()

        is_default = request.POST.get(
            'is_default'
        ) == 'on'

        # ---------------- REDIRECT URL ---------------- #

        redirect_url = reverse(
            'edit_address',
            kwargs={'id': id}
        )

        if next_url:
            redirect_url += f"?next={next_url}"

        # ---------------- REQUIRED FIELD VALIDATION ---------------- #

        if not all([
            full_name,
            phone_number,
            house_name,
            address,
            area,
            country,
            district,
            state,
            pincode,
            address_type
        ]):

            messages.error(
                request,
                "All fields are required"
            )

            return redirect(redirect_url)

        # ---------------- FULL NAME VALIDATION ---------------- #

        if len(full_name) < 3:
            messages.error(
                request,
                "Full name must contain at least 3 characters"
            )
            return redirect(redirect_url)

        if len(full_name) > 100:
            messages.error(
                request,
                "Full name is too long"
            )
            return redirect(redirect_url)

        if not re.match(r'^[A-Za-z\s]+$', full_name):
            messages.error(
                request,
                "Full name should contain only alphabets"
            )
            return redirect(redirect_url)

        if "  " in full_name:
            messages.error(
                request,
                "Full name contains invalid spaces"
            )
            return redirect(redirect_url)

        # ---------------- PHONE NUMBER VALIDATION ---------------- #

        if not phone_number.isdigit():
            messages.error(
                request,
                "Phone number must contain only digits"
            )
            return redirect(redirect_url)

        if len(phone_number) != 10:
            messages.error(
                request,
                "Phone number must contain exactly 10 digits"
            )
            return redirect(redirect_url)

        if not re.match(r'^[6-9]\d{9}$', phone_number):
            messages.error(
                request,
                "Invalid Indian phone number"
            )
            return redirect(redirect_url)

        # ---------------- HOUSE NAME VALIDATION ---------------- #

        if len(house_name) < 2:
            messages.error(
                request,
                "House name must contain at least 2 characters"
            )
            return redirect(redirect_url)

        if len(house_name) > 100:
            messages.error(
                request,
                "House name is too long"
            )
            return redirect(redirect_url)

        # ---------------- ADDRESS VALIDATION ---------------- #

        if len(address) < 10:
            messages.error(
                request,
                "Address must contain at least 10 characters"
            )
            return redirect(redirect_url)

        if len(address) > 300:
            messages.error(
                request,
                "Address is too long"
            )
            return redirect(redirect_url)

        # ---------------- AREA VALIDATION ---------------- #

        if len(area) < 2:
            messages.error(
                request,
                "Area name is too short"
            )
            return redirect(redirect_url)

        if len(area) > 100:
            messages.error(
                request,
                "Area name is too long"
            )
            return redirect(redirect_url)

        # ---------------- DISTRICT VALIDATION ---------------- #

        if len(district) < 2:
            messages.error(
                request,
                "District name is too short"
            )
            return redirect(redirect_url)

        if len(district) > 100:
            messages.error(
                request,
                "District name is too long"
            )
            return redirect(redirect_url)

        if not re.match(r'^[A-Za-z\s]+$', district):
            messages.error(
                request,
                "District name should contain only alphabets"
            )
            return redirect(redirect_url)

        # ---------------- STATE VALIDATION ---------------- #

        if len(state) < 2:
            messages.error(
                request,
                "State name is too short"
            )
            return redirect(redirect_url)

        if len(state) > 100:
            messages.error(
                request,
                "State name is too long"
            )
            return redirect(redirect_url)

        if not re.match(r'^[A-Za-z\s]+$', state):
            messages.error(
                request,
                "State name should contain only alphabets"
            )
            return redirect(redirect_url)

        # ---------------- COUNTRY VALIDATION ---------------- #

        if len(country) < 2:
            messages.error(
                request,
                "Country name is too short"
            )
            return redirect(redirect_url)

        if len(country) > 100:
            messages.error(
                request,
                "Country name is too long"
            )
            return redirect(redirect_url)

        if not re.match(r'^[A-Za-z\s]+$', country):
            messages.error(
                request,
                "Country name should contain only alphabets"
            )
            return redirect(redirect_url)

        # ---------------- PINCODE VALIDATION ---------------- #

        if not pincode.isdigit():
            messages.error(
                request,
                "Pincode must contain only digits"
            )
            return redirect(redirect_url)

        if len(pincode) != 6:
            messages.error(
                request,
                "Pincode must contain exactly 6 digits"
            )
            return redirect(redirect_url)

        if pincode.startswith('0'):
            messages.error(
                request,
                "Invalid pincode"
            )
            return redirect(redirect_url)

        # ---------------- ADDRESS TYPE VALIDATION ---------------- #

        allowed_address_types = [
            'Home',
            'Office',
            'Other'
        ]

        if address_type not in allowed_address_types:
            messages.error(
                request,
                "Invalid address type selected"
            )
            return redirect(redirect_url)

        # ---------------- DUPLICATE ADDRESS VALIDATION ---------------- #

        duplicate_address = Address.objects.filter(
            user=request.user,
            full_name__iexact=full_name,
            phone_number=phone_number,
            house_name__iexact=house_name,
            address__iexact=address,
            pincode=pincode
        ).exclude(id=id).exists()

        if duplicate_address:
            messages.error(
                request,
                "This address already exists"
            )
            return redirect(redirect_url)

        # ---------------- DEFAULT ADDRESS HANDLING ---------------- #

        if is_default:

            Address.objects.filter(
                user=request.user,
                is_default=True
            ).exclude(id=id).update(is_default=False)

        # ---------------- UPDATE ADDRESS ---------------- #

        address_obj.full_name = full_name.title()
        address_obj.phone_number = phone_number
        address_obj.house_name = house_name.title()
        address_obj.address = address
        address_obj.area = area.title()
        address_obj.country = country.title()
        address_obj.district = district.title()
        address_obj.state = state.title()
        address_obj.pincode = pincode
        address_obj.address_type = address_type
        address_obj.is_default = is_default

        address_obj.save()

        # ---------------- SUCCESS MESSAGE ---------------- #

        messages.success(
            request,
            "Address updated successfully"
        )

        if next_url == 'checkout':
            return redirect('checkout')

        return redirect('address_page')

    context = {
        'address': address_obj,
        'next': next_url
    }

    return render(
        request,
        'edit_address.html',
        context
    )


@login_required(login_url='login')
def delete_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    address.delete()

    messages.success(request, "Address deleted successfully")
    return redirect('address_page')