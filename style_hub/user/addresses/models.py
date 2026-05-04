from django.db import models
from django.conf import settings


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.state}"