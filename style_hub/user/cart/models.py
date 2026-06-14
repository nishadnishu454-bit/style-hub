from django.db import models
from django.contrib.auth import get_user_model
from admin_panel.variantmanagement.models import ProductVariant

User = get_user_model()

class Cart(models.Model):

    user = models.ForeignKey( User,on_delete=models.CASCADE,related_name='cart_items')
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE,related_name='cart_variant')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        return f"{self.user.username} - {self.variant}"