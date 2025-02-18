from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class BaseModel(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

class MarketMilkPrice(BaseModel):
    price = models.DecimalField(max_digits=100, decimal_places=2, db_index=True)

    def __str__(self):
        return f"{self.price}"

    def save(self, *args, **kwargs):
        # Deactivate all other active records for this author
        if self.is_active:
            MarketMilkPrice.objects.filter(author=self.author, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['price', 'created_at']),
            models.Index(fields=['author', 'is_active', 'created_at'])
        ]

class Collection(BaseModel):
    MEASURE_CHOICES = [
        ('liters', 'Liters'),
        ('kg', 'Kg')
    ]

    TIME_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening')
    ]
    
    MILK_TYPE_CHOICES = [
        ('cow', 'Cow'), 
        ('buffalo', 'Buffalo'),
        ('mix', 'Mix')
    ]
    
    collection_time = models.CharField(max_length=10, choices=TIME_CHOICES, db_index=True)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPE_CHOICES, db_index=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, db_index=True)
    collection_date = models.DateField(db_index=True)
    
    base_fat_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=6.5)
    base_snf_percentage = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=9.0,
        validators=[
            MinValueValidator(Decimal('9.0'), message="Base SNF percentage cannot be less than 9.0"),
            MaxValueValidator(Decimal('9.5'), message="Base SNF percentage cannot be more than 9.5")
        ]
    )
    
    measured = models.CharField(max_length=10, choices=MEASURE_CHOICES)
    liters = models.DecimalField(max_digits=6, decimal_places=2)
    kg = models.DecimalField(max_digits=6, decimal_places=2)
    fat_percentage = models.DecimalField(max_digits=4, decimal_places=2)
    fat_kg = models.DecimalField(max_digits=6, decimal_places=2)
    clr = models.DecimalField(max_digits=4, decimal_places=2)
    snf_percentage = models.DecimalField(max_digits=4, decimal_places=2)
    snf_kg = models.DecimalField(max_digits=6, decimal_places=2)

    fat_rate = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)
    snf_rate = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=50, decimal_places=2, db_index=True)
    amount = models.DecimalField(max_digits=100, decimal_places=2, db_index=True)

    def __str__(self):
        return f"{self.customer.name} - {self.collection_date} {self.collection_time}"

    class Meta:
        ordering = ['-collection_date', '-created_at']
        indexes = [
            models.Index(fields=['collection_date', 'collection_time']),
            models.Index(fields=['customer', 'collection_date']),
            models.Index(fields=['author', 'is_active', 'collection_date']),
            models.Index(fields=['milk_type', 'collection_date']),
            models.Index(fields=['rate', 'amount'])
        ]

class Customer(BaseModel):
    name = models.CharField(max_length=100, db_index=True)
    phone = models.CharField(max_length=15, blank=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Add +91 prefix to phone number if it doesn't exist
        if self.phone:
            # Remove any existing '+' or leading zeros
            cleaned_phone = self.phone.lstrip('+0')
            # Remove '91' prefix if it exists
            if cleaned_phone.startswith('91'):
                cleaned_phone = cleaned_phone[2:]
            # Add +91 prefix
            self.phone = f'+91{cleaned_phone}'
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['name', 'phone']),
            models.Index(fields=['author', 'is_active'])
        ]
        ordering = ['name', '-created_at']

class DairyInformation(BaseModel):
    RATE_TYPE_CHOICES = [
        ('fat_only', 'Fat Only'),
        ('fat_snf', 'Fat + SNF'),
        ('fat_clr', 'Fat + CLR')
    ]

    dairy_name = models.CharField(max_length=255, db_index=True)
    dairy_address = models.TextField(blank=True)
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, db_index=True)

    def __str__(self):
        return self.dairy_name

    def save(self, *args, **kwargs):
        # Deactivate all other active records for this author
        if self.is_active:
            DairyInformation.objects.filter(author=self.author, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dairy Information'
        verbose_name_plural = 'Dairy Information'
        indexes = [
            models.Index(fields=['dairy_name', 'rate_type']),
            models.Index(fields=['author', 'is_active', 'created_at'])
        ]