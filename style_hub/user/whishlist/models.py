from django.db import models
from django.contrib.auth import get_user_model
from admin_panel.productmanagement.models import ProductVariant

User = get_user_model()


class Wishlist(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlist_items')
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE,related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')
        ordering = ['-id']

    def __str__(self):
        return f"{self.user.username} - {self.variant.product.product_name}"