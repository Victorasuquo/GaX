from django.db import models
from django.conf import settings  
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid

# Custom user model
class User(AbstractUser):
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.username

# Profile model - Ensure defaults are handled
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,)  
    phone_number = models.CharField(max_length=15, unique=True, )  
    age = models.IntegerField(blank=True, null=True)
    balance = models.DecimalField(default=0.0, decimal_places=2, max_digits=12)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    bvn = models.CharField(max_length=11, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# BankAccount model - Correct default handling for datetime fields
class BankAccount(models.Model):
    ACCOUNT_TYPES = (
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use custom User model
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    balance = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate account number if not set
        if not self.account_number and self.user.phone_number:
            # Remove the first digit and ensure it is 10 digits
            cleaned_number = self.user.phone_number.lstrip('0')[:10]
            self.account_number = cleaned_number.zfill(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

# Transaction model - Handle default values and references correctly
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True)  
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=255, unique=True,  editable=False)
    is_approved = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(uuid.uuid4())
            super().save(*args, **kwargs)




    def __str__(self):
        return f"{self.transaction_type.title()} - ₦{self.amount}"

# BillPayment model - Handle default values for fields correctly
class BillPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use custom User model
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    biller_name = models.CharField(max_length=100)
    bill_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.biller_name} - ₦{self.amount}"

# KYC model - Handle default values for `status`
class KYC(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use custom User model
    id_document = models.FileField(upload_to='kyc_docs/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"KYC for {self.user.username} - {self.status}"
