from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=10,blank=True,null=True)
    profile_photo = models.ImageField(upload_to='profile_photo/', null=True,blank=True)
    is_email_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
    

class OTP(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.TimeField()


    
    def save(self, *args, **kwargs):
        if not self.expired_at:
            self.expired_at = timezone.now() + timedelta(seconds=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expired_at 


    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"