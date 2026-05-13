from django.db import models
from django.conf import settings
from admin_panel.productmanagement.models import ProductVariant
from user.addresses.models import Address


class Order(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash On Delivery'),('online', 'Online Payment'),('wallet', 'Wallet'),)

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),('paid', 'Paid'),('failed', 'Failed'), ('refunded', 'Refunded'),)

    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),('shipped', 'Shipped'), ('out_for_delivery', 'Out For Delivery'),('delivered', 'Delivered'),('cancelled', 'Cancelled'),)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='orders')

    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True,blank=True,related_name='orders')

    order_number = models.CharField(max_length=20, unique=True)

    payment_method = models.CharField(max_length=20,choices=PAYMENT_METHOD_CHOICES,default='cod')

    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES,default='pending' )

    order_status = models.CharField(max_length=30,choices=ORDER_STATUS_CHOICES, default='pending')

    subtotal = models.DecimalField( max_digits=10, decimal_places=2,default=0 )

    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0 )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField( auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):

    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')

    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE,related_name='order_items')

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    total_price = models.DecimalField(max_digits=10,decimal_places=2 )

    created_at = models.DateTimeField( auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} - {self.variant.product.product_name}"