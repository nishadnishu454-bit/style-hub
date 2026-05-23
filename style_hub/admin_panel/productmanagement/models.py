from django.db import models
from admin_panel.categorymanagement.models import Category
# Create your models here.
class Product(models.Model):

    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    product_name = models.CharField(max_length=150)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.product_name
    

class ProductVariant(models.Model):

    product = models.ForeignKey(Product,on_delete=models.CASCADE, related_name='variants' )
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=30)
    variant_price = models.DecimalField( max_digits=10,  decimal_places=2 )
    variant_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        return f"{self.product.product_name} - {self.size} - {self.color}"

    @property
    def offer_price(self):
        from decimal import Decimal
        from django.utils import timezone
        today = timezone.now().date()
        product_offers = self.product.offers.filter(is_active=True, is_deleted=False, start_date__lte=today, end_date__gte=today)
        
        if self.product.category.is_active and not self.product.category.is_deleted:
            category_offers = self.product.category.offers.filter(is_active=True, is_deleted=False, start_date__lte=today, end_date__gte=today)
        else:
            category_offers = self.product.category.offers.none()
        
        max_discount = Decimal('0.00')
        price = self.variant_price
        
        for offer in list(product_offers) + list(category_offers):
            if offer.discount_type == 'PERCENTAGE':
                discount = (price * offer.discount_value) / Decimal('100.00')
            else:
                discount = offer.discount_value
            if discount > max_discount:
                max_discount = discount
                
        discounted_price = price - max_discount
        return max(discounted_price, Decimal('0.00')).quantize(Decimal('0.01'))

    @property
    def has_active_offer(self):
        return self.offer_price < self.variant_price


class ProductVariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variant_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Offer(models.Model):
    DISCOUNT_TYPES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    )
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
