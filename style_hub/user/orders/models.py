from django.db import models
from django.conf import settings
from user.addresses.models import Address
from admin_panel.productmanagement.models import Product
from admin_panel.variantmanagement.models import ProductVariant


class Order(models.Model):

    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('RAZORPAY', 'Razorpay'),
        ('WALLET', 'Wallet'),
        ('UPI', 'UPI'),
    )

    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )

    ORDER_STATUS = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
        ('Return Rejected', 'Return Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_orders')
    address = models.OneToOneField('OrderAddress',on_delete=models.SET_NULL, null=True, blank=True,related_name='order')
    order_number = models.CharField(max_length=50, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refunded_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    reason = models.TextField(null=True, blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    coupon = models.ForeignKey('couponmanagement.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):

    ITEM_STATUS = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),

        ('Partially Cancelled', 'Partially Cancelled'),
        ('Cancelled', 'Cancelled'),

        ('Return Requested', 'Return Requested'),
        ('Partially Returned', 'Partially Returned'),
        ('Returned', 'Returned'),

        ('Return Rejected', 'Return Rejected'),
    )

    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    variant = models.ForeignKey( ProductVariant, on_delete=models.SET_NULL,null=True,blank=True )
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    cancelled_quantity = models.PositiveIntegerField(default=0)
    returned_quantity = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_status = models.CharField(max_length=30,choices=ITEM_STATUS,default='Pending')
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def remaining_quantity(self):
        return (
            self.quantity - self.cancelled_quantity - self.returned_quantity)

    def __str__(self):
        return self.product_name
    




class OrderAddress(models.Model):
    full_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=12)
    house_name = models.CharField(max_length=30)
    address = models.TextField()
    area = models.CharField(max_length=30)
    country = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=30)
    pincode = models.CharField(max_length=30)
    address_type = models.CharField(max_length=30)

    def __str__(self):
        return self.full_name





class Review(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'order_item')

    def __str__(self):
        return f"{self.user.username} - {self.product.product_name}"


class ReviewImage(models.Model):

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.review.title}"
    



    