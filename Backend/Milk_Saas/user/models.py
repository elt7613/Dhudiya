from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class CustomUserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def create_user(self, username, phone_number, password=None, **extra_fields):
        if not username and not phone_number:
            raise ValueError('Either username or phone number must be set')
        
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
        return self.create_user(username, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Add reset password fields
    reset_password_token = models.CharField(max_length=6, blank=True, null=True)
    reset_password_token_created_at = models.DateTimeField(blank=True, null=True)

    # Managers
    objects = CustomUserManager()  # Returns only active users
    all_objects = models.Manager()  # Can return all users including inactive

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']

    def soft_delete(self):
        self.is_active = False
        self.save()

    def create_reset_password_token(self):
        """Create a 6-digit OTP and save it with timestamp"""
        from django.utils import timezone
        import random
        
        self.reset_password_token = str(random.randint(100000, 999999))
        self.reset_password_token_created_at = timezone.now()
        self.save()
        return self.reset_password_token

    def verify_reset_password_token(self, token):
        """Verify if the token is valid and not expired"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.reset_password_token or not self.reset_password_token_created_at:
            return False
            
        # Check if token is expired (10 minutes validity)
        if timezone.now() > self.reset_password_token_created_at + timedelta(minutes=10):
            return False
            
        return self.reset_password_token == token

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['phone_number']),
        ]
