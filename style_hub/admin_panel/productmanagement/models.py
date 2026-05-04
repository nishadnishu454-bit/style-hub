from django.db import models
from admin_panel.categorymanagement.models import Category
# Create your models here.
class Product(models.Model):

    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    product_name = models.CharField(max_length=150)
    description = models.TextField()
    product_image = models.ImageField(upload_to='product_images/',blank=True,null=True)
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.product_name