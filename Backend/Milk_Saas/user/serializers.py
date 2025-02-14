from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'phone_number', 'email', 'password')
        extra_kwargs = {
            'email': {'required': False},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.Serializer):
    login_field = serializers.CharField()
    password = serializers.CharField()

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