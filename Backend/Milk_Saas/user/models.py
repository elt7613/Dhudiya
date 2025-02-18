from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone
import random
import string
import logging

logger = logging.getLogger('user')

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class CustomUserManager(BaseUserManager):
    def get_queryset(self):
        # By default, filter to only active users
        return super().get_queryset().filter(is_active=True)

    def get_all(self):
        # Method to get all users including inactive ones
        return super().get_queryset()

    def filter(self, *args, **kwargs):
        # For direct filtering, use the active users queryset
        return self.get_queryset().filter(*args, **kwargs)

    def create_user(self, username, phone_number, password=None, **extra_fields):
        if not username and not phone_number:
            raise ValueError('Either username or phone number must be set')
        
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        if not username:
            username = self.generate_unique_username(phone_number)
        
        user = self.model(
            username=username,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(username, phone_number, password, **extra_fields)

    def generate_unique_username(self, phone_number):
        """Generate a unique username based on phone number"""
        base = f"user_{phone_number[-6:]}"
        username = base
        counter = 1
        
        while self.filter(username=username).exists():
            username = f"{base}_{counter}"
            counter += 1
            
        return username

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[MinLengthValidator(3)]
    )
    phone_regex = RegexValidator(
        regex=r'^[1-9]\d{9}$',
        message="Phone number must be a 10-digit number starting with 6-9."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=13,  # +91 + 10 digits
        unique=True,
        db_index=True
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    referral_code = models.CharField(
        max_length=5,
        unique=True,
        blank=True,
        null=True,
        db_index=True
    )

    # Add reset password fields
    reset_password_token = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )
    reset_password_token_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # Managers
    objects = CustomUserManager()  # Returns only active users
    all_objects = models.Manager()  # Can return all users including inactive

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f"{self.username} ({self.phone_number})"

    def save(self, *args, **kwargs):
        # Format phone number to include +91
        if self.phone_number and not self.phone_number.startswith('+91'):
            self.phone_number = f'+91{self.phone_number}'
        
        if not self.referral_code:
            self.referral_code = self.generate_unique_referral_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_referral_code():
        """Generate a unique 5 character referral code"""
        attempts = 0
        max_attempts = 5
        
        while attempts < max_attempts:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            if not User.objects.filter(referral_code=code).exists():
                return code
            attempts += 1
            
        # If we couldn't generate a unique code after max attempts,
        # generating a longer one as fallback
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def soft_delete(self):
        """Soft delete the user"""
        self.is_active = False
        self.save(update_fields=['is_active'])

    def create_reset_password_token(self):
        """Create a 6-digit OTP and save it with timestamp"""
        otp = str(random.randint(100000, 999999))
        self.reset_password_token = otp
        self.reset_password_token_created_at = timezone.now()
        self.save(update_fields=['reset_password_token', 'reset_password_token_created_at'])
        return otp

    def verify_reset_password_token(self, token):
        """Verify if the token is valid and not expired"""
        if not self.reset_password_token or not self.reset_password_token_created_at:
            return False
            
        # Check if token is expired (10 minutes validity)
        if timezone.now() > self.reset_password_token_created_at + timezone.timedelta(minutes=10):
            return False
            
        return self.reset_password_token == token

class ReferralUsage(models.Model):
    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referrals_given',
        db_index=True
    )
    referred_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referral_used',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_rewarded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('referrer', 'referred_user')
        indexes = [
            models.Index(fields=['referrer', 'created_at']),
            models.Index(fields=['referred_user', 'created_at']),
            models.Index(fields=['is_rewarded']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"

    def save(self, *args, **kwargs):
        if self.referrer_id == self.referred_user_id:
            raise ValueError("A user cannot refer themselves")
        super().save(*args, **kwargs)
