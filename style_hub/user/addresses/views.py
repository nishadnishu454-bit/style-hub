from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address
from django.db.models import Q


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

    return render(request, 'address.html', {'address': address})


@login_required(login_url='login')
def add_address_page(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        house_name = request.POST.get('house_name')
        address = request.POST.get('address')
        area = request.POST.get('area')
        country = request.POST.get('country')
        district = request.POST.get('district')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        address_type = request.POST.get('address_type')
        is_default = request.POST.get('is_default') == 'on'

        if not full_name or not phone_number or not house_name or not address or not area or not country or not district or not state or not pincode or not address_type:
            messages.error(request, "All fields are required")
            return redirect('add_address')

        if not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, "Invalid phone number")
            return redirect('add_address')

        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Invalid pincode")
            return redirect('add_address')

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone_number,
            house_name=house_name,
            address=address,
            area=area,
            country=country,
            district=district,
            state=state,
            pincode=pincode,
            address_type=address_type,
            is_default=is_default
        )

        messages.success(request, "Address added successfully")
        return redirect('address_page')

    return render(request, 'add_address.html')


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
    address_obj = get_object_or_404(Address, id=id, user=request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        house_name = request.POST.get('house_name')
        address = request.POST.get('address')
        area = request.POST.get('area')
        country = request.POST.get('country')
        district = request.POST.get('district')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        address_type = request.POST.get('address_type')
        is_default = request.POST.get('is_default') == 'on'

        if not full_name or not phone_number or not house_name or not address or not area or not country or not district or not state or not pincode or not address_type:
            messages.error(request, "All fields are required")
            return redirect('edit_address', id=id)

        if not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, "Invalid phone number")
            return redirect('edit_address', id=id)

        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Invalid pincode")
            return redirect('edit_address', id=id)

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).exclude(id=id).update(is_default=False)

        address_obj.full_name = full_name
        address_obj.phone_number = phone_number
        address_obj.house_name = house_name
        address_obj.address = address
        address_obj.area = area
        address_obj.country = country
        address_obj.district = district
        address_obj.state = state
        address_obj.pincode = pincode
        address_obj.address_type = address_type
        address_obj.is_default = is_default
        address_obj.save()

        messages.success(request, "Address updated successfully")
        return redirect('address_page')

    return render(request, 'edit_address.html', {'address': address_obj})


@login_required(login_url='login')
def delete_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    address.delete()

    messages.success(request, "Address deleted successfully")
    return redirect('address_page')