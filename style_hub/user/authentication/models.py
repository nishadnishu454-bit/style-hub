from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import uuid

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=10,blank=True,null=True)
    profile_photo = models.ImageField(upload_to='profile_photo/', null=True,blank=True)
    is_email_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_users')
    
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = str(uuid.uuid4()).replace('-', '')[:8].upper()
            while CustomUser.objects.filter(referral_code=code).exists():
                code = str(uuid.uuid4()).replace('-', '')[:8].upper()
            self.referral_code = code
        super().save(*args, **kwargs)


class Referral(models.Model):
    referrer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_sent')
    referred_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='referral_received')
    benefit_amount_referred = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    benefit_amount_referrer = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    is_referrer_rewarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"
    

class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.username} - {self.code}"