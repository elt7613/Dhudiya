from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import User, ReferralUsage

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'phone_number', 'email', 'password', 'referral_code')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=10)

    class Meta:
        model = User
        fields = ('id', 'username', 'phone_number', 'email', 'password', 'referral_code')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_phone_number(self, value):
        # Remove any spaces or special characters
        value = ''.join(filter(str.isdigit, value))
        
        # Validate length
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
    
        # Check if phone number already exists (with +91)
        if User.objects.filter(phone_number=f'+91{value}').exists():
            raise serializers.ValidationError("This phone number is already registered.")
            
        return value

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        # Phone number will be formatted to include +91 in the model's save method
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    login_field = serializers.CharField()
    password = serializers.CharField()

    def validate_login_field(self, value):
        # If the login field is a phone number, format it
        if value.isdigit() and len(value) == 10:
            return f'+91{value}'
        return value

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            if not user.verify_reset_password_token(data['otp']):
                raise serializers.ValidationError({
                    "otp": "Invalid or expired OTP."
                })
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "No user found with this email address."
            })
        return data

class ApplyReferralCodeSerializer(serializers.Serializer):
    referral_code = serializers.CharField(max_length=5)

    def validate_referral_code(self, value):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        try:
            referrer = User.objects.get(referral_code=value)
            
            # Check if user is trying to use their own code
            if referrer == request.user:
                raise serializers.ValidationError("Cannot use your own referral code")
            
            # Check if user has already used any referral code
            if ReferralUsage.objects.filter(referred_user=request.user).exists():
                raise serializers.ValidationError("You have already used a referral code")
                
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid referral code") 