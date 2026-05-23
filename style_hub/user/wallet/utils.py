from decimal import Decimal
from .models import Wallet, WalletTransaction


def credit_wallet(user, amount, purpose, order=None):

    amount = Decimal(amount)

    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': 0}
    )

    wallet.balance += amount
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
        defaults={'balance': 0}
    )

    if wallet.balance < amount:
        return False

    wallet.balance -= amount
    wallet.save()

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