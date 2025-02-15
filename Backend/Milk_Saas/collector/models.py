from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
# Milk Price According to market
class MarketMilkPrice(models.Model):
    price = models.DecimalField(max_digits=100, decimal_places=2)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.price}"
    
    def soft_delete(self):
        self.is_active = False
        self.save()
    
# User's Rate Step (formerly RateChart)
class RateStep(models.Model):
    RATE_TYPE_CHOICES = [
        ('rate per kg', 'Rate per kg')
    ]

    MILK_TYPE_CHOICES = [
        ('cow', 'Cow'),
        ('buffalo', 'Buffalo')
    ]

    rate_type = models.CharField(max_length=50, choices=RATE_TYPE_CHOICES)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPE_CHOICES)

    fat_from = models.DecimalField(max_digits=4, decimal_places=2)
    fat_to = models.DecimalField(max_digits=4, decimal_places=2)
    fat_rate = models.DecimalField(max_digits=6, decimal_places=2)

    snf_from = models.DecimalField(max_digits=4, decimal_places=2)
    snf_to = models.DecimalField(max_digits=4, decimal_places=2)
    snf_rate = models.DecimalField(max_digits=6, decimal_places=2)

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.milk_type} - {self.rate_type}"

    def soft_delete(self):
        self.is_active = False
        self.save()

# User's Collection
class Collection(models.Model):
    MEASURE_CHOICES = [
        ('liters', 'Liters'),
        ('kg', 'Kg')
    ]

    # Time choices
    TIME_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening')
    ]
    
    # Milk type choices
    MILK_TYPE_CHOICES = [
        ('cow', 'Cow'),
        ('buffalo', 'Buffalo')
    ]
    
    # Collection details
    collection_time = models.CharField(max_length=10, choices=TIME_CHOICES)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPE_CHOICES)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    collection_date = models.DateField()
    
    # Milk parameters
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
    rate = models.DecimalField(max_digits=50, decimal_places=2)

    amount = models.DecimalField(max_digits=100, decimal_places=2)
    
    # Timestamps and status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Managers
    objects = ActiveManager()  # Returns only active records
    all_objects = models.Manager()  # Can return all records including inactive
    
    def __str__(self):
        return f"{self.customer} - {self.collection_date} {self.collection_time}"
    
    def soft_delete(self):
        self.is_active = False
        self.save()
    
    class Meta:
        ordering = ['-collection_date', '-created_at']

# User's Customer
class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Managers
    objects = ActiveManager()  # Returns only active records
    all_objects = models.Manager()  # Can return all records including inactive
    
    def __str__(self):
        return self.name
    
    def soft_delete(self):
        self.is_active = False
        self.save()

class DairyInformation(models.Model):
    RATE_TYPE_CHOICES = [
        ('fat_only', 'Fat Only'),
        ('fat_snf', 'Fat + SNF'),
        ('fat_clr', 'Fat + CLR')
    ]

    dairy_name = models.CharField(max_length=255)
    dairy_address = models.TextField(blank=True)
    rate_type = models.CharField(max_length=20,choices=RATE_TYPE_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.dairy_name} - {self.get_rate_type_display()}"

    def soft_delete(self):
        self.is_active = False
        self.save()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dairy Information'
        verbose_name_plural = 'Dairy Information'