from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class SoftDeletionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet', db_index=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                validators=[MinValueValidator(Decimal('0.00'))])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = SoftDeletionManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.user.username}'s Wallet - ₹{self.balance}"

    def add_balance(self, amount):
        """Safely add amount to balance ensuring Decimal type"""
        if Decimal(str(amount)) <= 0:
            raise ValueError("Amount must be greater than 0")
        self.balance = Decimal(str(self.balance)) + Decimal(str(amount))
        self.save(update_fields=['balance', 'updated_at'])

    def subtract_balance(self, amount):
        """Safely subtract amount from balance ensuring Decimal type"""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance = Decimal(str(self.balance)) - amount
        self.save(update_fields=['balance', 'updated_at'])

    def set_balance(self, amount):
        """Safely set balance ensuring Decimal type"""
        amount = Decimal(str(amount))
        if amount < 0:
            raise ValueError("Balance cannot be negative")
        self.balance = amount
        self.save(update_fields=['balance', 'updated_at'])

    def soft_delete(self):
        """Soft delete the wallet"""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=['is_deleted', 'is_active', 'updated_at'])

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_deleted']),
        ]

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    TRANSACTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='PENDING', db_index=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = SoftDeletionManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - ₹{self.amount}"

    def clean(self):
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if self.transaction_type not in dict(self.TRANSACTION_TYPE_CHOICES):
            raise ValueError("Invalid transaction type")
        if self.status not in dict(self.TRANSACTION_STATUS_CHOICES):
            raise ValueError("Invalid status")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Soft delete the transaction"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type', 'status']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['is_deleted']),
        ]
