from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.exceptions import ValidationError
from rest_framework.permissions import AllowAny
import logging
from .email_utils import send_reset_password_email

logger = logging.getLogger('user')
User = get_user_model()

class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '20/minute'

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                token = RefreshToken.for_user(user)
                
                response_data = {
                    'token': str(token.access_token),
                    'message': 'Registration successful'
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except ValidationError as e:
            logger.warning(f"Validation error during registration: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                login_field = serializer.validated_data['login_field']
                password = serializer.validated_data['password']
                
                # Check failed login attempts
                cache_key = f"login_attempts_{login_field}"
                failed_attempts = cache.get(cache_key, 0)
                
                if failed_attempts >= 5:  # Lock after 5 failed attempts
                    return Response({
                        'error': 'Too many failed attempts. Please try again later.'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                user = authenticate(request, username=login_field, password=password)
                
                if not user:
                    try:
                        user_obj = User.objects.get(phone_number=login_field)
                        user = authenticate(
                            request,
                            username=user_obj.username,
                            password=password
                        )
                    except User.DoesNotExist:
                        user = None

                if user:
                    if not user.is_active:
                        return Response({
                            'error': 'Account is disabled'
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    # Reset failed attempts on successful login
                    cache.delete(cache_key)
                    
                    token = RefreshToken.for_user(user)
                    return Response({
                        'token': str(token.access_token),
                        'message': 'Login successful',
                        'user': {
                            'username': user.username,
                            'phone_number': user.phone_number,
                            'email': user.email
                        }
                    }, status=status.HTTP_200_OK)
                
                # Increment failed attempts
                cache.set(cache_key, failed_attempts + 1, timeout=300)  # 5 minutes timeout
                
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            serializer = ForgotPasswordSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response({
                        'error': 'No user found with this email address.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Generate OTP
                otp = user.create_reset_password_token()
                
                # Send email
                email_sent = send_reset_password_email(email, otp)
                
                if email_sent:
                    return Response({
                        'message': 'Password reset OTP has been sent to your email.',
                        'email': email  # Return partial email for UI display
                    }, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Failed to send reset password email to {email}")
                    return Response({
                        'error': 'Failed to send reset password email. Please try again later.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in forgot password: {str(e)}")
            return Response({
                'error': 'An unexpected error occurred. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            serializer = ResetPasswordSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                otp = serializer.validated_data['otp']
                new_password = serializer.validated_data['new_password']

                try:
                    user = User.objects.get(email=email)
                    
                    # Verify OTP
                    if not user.verify_reset_password_token(otp):
                        return Response({
                            'error': 'Invalid or expired OTP.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Set new password
                    user.set_password(new_password)
                    # Clear reset token
                    user.reset_password_token = None
                    user.reset_password_token_created_at = None
                    user.save()
                    
                    return Response({
                        'message': 'Password has been reset successfully.'
                    }, status=status.HTTP_200_OK)
                    
                except User.DoesNotExist:
                    return Response({
                        'error': 'User not found.'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in reset password: {str(e)}")
            return Response({
                'error': 'An unexpected error occurred. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)