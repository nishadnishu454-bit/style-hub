from django.db import models
from django.conf import settings
from user.orders.models import Order


class Wallet(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='wallet')
    balance = models.DecimalField( max_digits=10,decimal_places=2,default=0.00)
    created_at = models.DateTimeField( auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Wallet"



class WalletTransaction(models.Model):

    TRANSACTION_TYPE = (('credit', 'Credit'),('debit', 'Debit'),)
    STATUS_CHOICES = ( ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'),)
    PAYMENT_METHODS = ( ('razorpay', 'Razorpay'),('upi', 'UPI'),('card', 'Card'),('netbanking', 'Net Banking'),('wallet', 'Wallet'),('cod', 'Cash On Delivery'),)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE,related_name='transactions')
    order = models.ForeignKey(Order,on_delete=models.SET_NULL,null=True,blank=True,related_name='wallet_transactions')
    type = models.CharField(max_length=10,choices=TRANSACTION_TYPE)
    payment_method = models.CharField(max_length=20,choices=PAYMENT_METHODS,null=True,blank=True)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='completed')
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True )
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.wallet.user.username} - {self.type} - ₹{self.amount}"