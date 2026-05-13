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



class ProductVariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variant_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
