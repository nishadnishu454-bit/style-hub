from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q,F
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Wallet, WalletTransaction
import razorpay
from django.http import JsonResponse
from django.conf import settings
# Create your views here.


@login_required(login_url='login')
def wallet_page(request):

    search=request.GET.get('search','')
    transaction_type=request.GET.get('type','')

    wallet, created = Wallet.objects.get_or_create(
         user=request.user,
         defaults={'balance':0}
         )

    transactions = WalletTransaction.objects.filter(
        wallet=wallet
        ).order_by('-id')

    if search:

        try:
            search_id = int(search)
            transactions = transactions.filter(
                Q(purpose__icontains=search) |
                Q(status__icontains=search) |
                Q(id = search_id)
            )
                
        except ValueError:
                transactions = transactions.filter(
                    Q(purpose__icontains=search) |
                    Q(status__icontains=search)
                )
                
    if transaction_type:
        transactions=transactions.filter(type=transaction_type)

    paginator = Paginator(transactions,5)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)


    context={
        'wallet':wallet,
        'transactions':transactions,
        'search':search,
        'transaction_type':transaction_type
    }

    return render(request,'wallet.html',context)




client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


@login_required(login_url='login')
def add_money(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')

        if not amount:
             return JsonResponse({
                'success': False,
                'message': 'Please enter amount'
            },status=400)
        
        try:
            amount = Decimal(amount)

            if amount <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid amount'
                },status=400)
            
        except:
            return JsonResponse({
                'success': False,
                'message': 'Invalid amount'
            },status=400)
        
        razorpay_order = client.order.create({
            "amount": int(amount * 100),
            "currency": "INR",
            "payment_capture": "1"
        })

        request.session['wallet_topup_amount'] = str(amount)

        return JsonResponse({
            'success': True,
            'razorpay': True,
            'order_id': razorpay_order['id'],
            'amount': int(amount * 100),
            'key': settings.RAZORPAY_KEY_ID,
            'name': 'STYLE-HUB',
            'description': 'Wallet Topup',
        },status=200)
    

    return JsonResponse({'success': False,'message': 'Invalid request' },status=400)
    



@login_required(login_url='login')
def verify_wallet_payment(request):

    if request.method == 'POST':

        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

      
        try:
            razorpay_order = client.order.fetch(razorpay_order_id)
            amount = Decimal(razorpay_order['amount']) / 100
        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Could not verify order amount'
            },status=400)

        try:
            
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

       
            wallet, created = Wallet.objects.get_or_create(
                user=request.user,
                defaults={'balance': 0}
            )

            
            Wallet.objects.filter(id=wallet.id).update(
                balance=F('balance') + amount
            )

         
            WalletTransaction.objects.create(
                wallet=wallet,
                type='credit',
                purpose='Wallet Topup',
                amount=amount,
                status='completed',
                payment_method='razorpay'
            )

            return JsonResponse({
                'success': True,
                'message': 'Money added successfully'
            },status=200)

        except Exception as error:
            return JsonResponse({
                'success': False,
                'message': str(error)
            },status=500)

    return JsonResponse({'success': False,'message': 'Invalid request'},status=400)