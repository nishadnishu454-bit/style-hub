from decimal import Decimal
from .models import Wallet, WalletTransaction
from django.db.models import F


def credit_wallet(user, amount, purpose, order=None):

    amount = Decimal(amount)

    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('0.00')}
    )

    if not created:
        Wallet.objects.filter(id=wallet.id).update(balance=F('balance') + amount)
        wallet.refresh_from_db()
    else:
        wallet.balance = amount
        wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        order=order,
        type='credit',
        purpose=purpose,
        amount=amount,
        status='completed',
        payment_method='wallet'
    )


def debit_wallet(user, amount, purpose, order=None):
    amount = Decimal(amount)

    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('0.00')}
    )

    if wallet.balance < amount:
        return False

    Wallet.objects.filter(id=wallet.id).update(balance=F('balance') - amount)
    wallet.refresh_from_db()

    WalletTransaction.objects.create(
        wallet=wallet,
        order=order,
        type='debit',
        purpose=purpose,
        amount=amount,
        status='completed',
        payment_method='wallet'
    )

    return True