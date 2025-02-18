from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q, Prefetch
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, UserSerializer, ApplyReferralCodeSerializer
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from .models import User, ReferralUsage
from wallet.models import Wallet, WalletTransaction
from decimal import Decimal
import logging
from .email_utils import send_reset_password_email
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from rest_framework.exceptions import Throttled
import time
from rest_framework.exceptions import NotAuthenticated

logger = logging.getLogger('user')
User = get_user_model()

class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '20/minute'

    def throttle_failure(self):
        """Custom throttle failure handling with detailed response"""
        wait = self.wait()
        raise Throttled(detail={
            'error': 'Request was throttled',
            'wait_seconds': int(wait)
        })

class BaseAPIView(APIView):
    """Base class for common API functionality"""
    
    def handle_exception(self, exc):
        """Centralized exception handling"""
        if isinstance(exc, ValidationError):
            logger.warning(f"Validation error: {str(exc)}")
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(exc, NotAuthenticated):
            return Response(
                {'detail': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class UserRegistrationView(BaseAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    @transaction.atomic
    def post(self, request):
        try:
            start_time = time.time()
            serializer = UserRegistrationSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            referral_code = request.data.get('referral_code')
            user = serializer.save()
            wallet = user.wallet  # Get the wallet created by signal

            if referral_code:
                self._handle_referral(user, referral_code, wallet)

            # Generate access token for the user
            token = AccessToken.for_user(user)
            
            # Log performance metrics
            execution_time = time.time() - start_time
            logger.info(f"User registration completed in {execution_time:.2f} seconds")
            
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': serializer.data,
                    'referral_code': user.referral_code,
                    'token': str(token)
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as exc:
            return self.handle_exception(exc)

    def _handle_referral(self, user, referral_code, wallet):
        """Handle referral code logic"""
        try:
            referrer = User.objects.select_related('wallet').get(referral_code=referral_code)
            
            if not ReferralUsage.objects.filter(referred_user=user).exists():
                ReferralUsage.objects.create(
                    referrer=referrer,
                    referred_user=user,
                    is_rewarded=True
                )
                
                # Add bonus to referrer's wallet (₹50)
                referrer_wallet = referrer.wallet
                referrer_bonus = Decimal('50.00')
                WalletTransaction.objects.create(
                    wallet=referrer_wallet,
                    amount=referrer_bonus,
                    transaction_type='CREDIT',
                    status='SUCCESS',
                    description='Referral bonus for referring a new user'
                )
                referrer_wallet.add_balance(referrer_bonus)
                
                # Add bonus to new user's wallet (₹30)
                user_bonus = Decimal('30.00')
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=user_bonus,
                    transaction_type='CREDIT',
                    status='SUCCESS',
                    description='Welcome bonus for using referral code'
                )
                wallet.add_balance(user_bonus)
                
        except User.DoesNotExist:
            raise ValidationError('Invalid referral code')

class UserLoginView(BaseAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            start_time = time.time()
            serializer = UserLoginSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            login_field = serializer.validated_data['login_field']
            password = serializer.validated_data['password']
            
            # Check failed login attempts with exponential backoff
            cache_key = f"login_attempts_{login_field}"
            failed_attempts = cache.get(cache_key, 0)
            
            if failed_attempts >= 5:
                lockout_time = min(2 ** (failed_attempts - 4), 30)  # Max 30 minutes
                return Response({
                    'error': f'Too many failed attempts. Please try again in {lockout_time} minutes.',
                    'lockout_minutes': lockout_time
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            user = self._authenticate_user(request, login_field, password)
            
            if user:
                if not user.is_active:
                    return Response({
                        'error': 'Account is disabled'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Reset failed attempts on successful login
                cache.delete(cache_key)
                
                # Generate access token
                token = AccessToken.for_user(user)
                
                # Log performance metrics
                execution_time = time.time() - start_time
                logger.info(f"User login completed in {execution_time:.2f} seconds")
                
                return Response({
                    'token': str(token),
                    'message': 'Login successful',
                    'user': {
                        'username': user.username,
                        'phone_number': user.phone_number,
                        'email': user.email
                    }
                }, status=status.HTTP_200_OK)
            
            # Increment failed attempts with appropriate timeout
            timeout = min(300 * (2 ** (failed_attempts)), 1800)  # Max 30 minutes
            cache.set(cache_key, failed_attempts + 1, timeout=timeout)
            
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as exc:
            return self.handle_exception(exc)

    def _authenticate_user(self, request, login_field, password):
        """Authenticate user with username or phone number"""
        user = authenticate(request, username=login_field, password=password)
        
        if not user:
            try:
                user_obj = User.objects.only('username').get(phone_number=login_field)
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                return None
                
        return user

class ForgotPasswordView(BaseAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            start_time = time.time()
            serializer = ForgotPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            
            # Rate limit password reset requests per email
            cache_key = f"pwd_reset_{email}"
            reset_count = cache.get(cache_key, 0)
            
            if reset_count >= 3:  # Limit to 3 requests per hour
                return Response({
                    'error': 'Too many password reset attempts. Please try again in 1 hour.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            try:
                user = User.objects.only('email', 'username').get(email=email)
            except User.DoesNotExist:
                # Use same response time for security
                time.sleep(0.1)
                return Response({
                    'message': 'If a user with this email exists, a password reset OTP has been sent.'
                }, status=status.HTTP_200_OK)
            
            # Generate and save OTP
            otp = user.create_reset_password_token()
            
            # Send email with retries
            email_sent = send_reset_password_email(email, otp)
            
            if not email_sent:
                # Clear the OTP if email sending failed
                user.reset_password_token = None
                user.reset_password_token_created_at = None
                user.save(update_fields=['reset_password_token', 'reset_password_token_created_at'])
                
                logger.error(f"Failed to send OTP email to {email}")
                return Response({
                    'error': 'Failed to send reset password email. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Increment reset count with 1-hour expiry
            cache.set(cache_key, reset_count + 1, timeout=3600)
            
            # Log performance metrics
            execution_time = time.time() - start_time
            logger.info(f"Password reset request completed in {execution_time:.2f} seconds for {email}")
            
            return Response({
                'message': 'Password reset OTP has been sent to your email. Please check your inbox and spam folder.'
            }, status=status.HTTP_200_OK)
            
        except Exception as exc:
            logger.error(f"Unexpected error in forgot password: {str(exc)}")
            return self.handle_exception(exc)

    def _mask_email(self, email):
        """Mask email for security (e.g., j***@example.com)"""
        try:
            username, domain = email.split('@')
            masked_username = username[0] + '*' * (len(username) - 1)
            return f"{masked_username}@{domain}"
        except:
            return '****@****.***'

class ResetPasswordView(BaseAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            start_time = time.time()
            serializer = ResetPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']

            # Rate limit password reset attempts per email
            cache_key = f"pwd_reset_attempts_{email}"
            attempt_count = cache.get(cache_key, 0)
            
            if attempt_count >= 5:  # Limit to 5 attempts per 30 minutes
                return Response({
                    'error': 'Too many password reset attempts. Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            try:
                user = User.objects.get(email=email)
                
                # Verify OTP
                if not user.verify_reset_password_token(otp):
                    # Increment attempt count with 30 minutes expiry
                    cache.set(cache_key, attempt_count + 1, timeout=1800)
                    return Response({
                        'error': 'Invalid or expired OTP.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set new password
                user.set_password(new_password)
                # Clear reset token
                user.reset_password_token = None
                user.reset_password_token_created_at = None
                user.save(update_fields=['password', 'reset_password_token', 'reset_password_token_created_at'])
                
                # Clear all rate limiting caches for this email
                cache.delete(f"pwd_reset_{email}")
                cache.delete(cache_key)
                
                # Log performance metrics
                execution_time = time.time() - start_time
                logger.info(f"Password reset completed in {execution_time:.2f} seconds")
                
                return Response({
                    'message': 'Password has been reset successfully.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Use same response time for security
                time.sleep(0.1)
                return Response({
                    'error': 'Invalid or expired OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as exc:
            return self.handle_exception(exc)

class UserInfoView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            start_time = time.time()
            
            # Use select_related to optimize the query for wallet
            user = User.objects.select_related('wallet').prefetch_related(
                Prefetch(
                    'referrals_given',
                    queryset=ReferralUsage.objects.select_related('referred_user').filter(is_rewarded=True),
                    to_attr='successful_referrals'
                )
            ).get(id=request.user.id)
            
            # Get wallet balance
            wallet_balance = user.wallet.balance if hasattr(user, 'wallet') else Decimal('0.00')
            
            response_data = {
                'user_details': {
                    'username': user.username,
                    'phone_number': user.phone_number,
                    'email': user.email,
                    'date_joined': user.date_joined,
                    'referral_code': user.referral_code
                },
                'wallet': {
                    'balance': str(wallet_balance),
                    'currency': '₹'
                }
            }
            
            # Log performance metrics
            execution_time = time.time() - start_time
            logger.info(f"User info retrieved in {execution_time:.2f} seconds")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as exc:
            return self.handle_exception(exc)

class ApplyReferralCodeView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomAnonRateThrottle]

    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            serializer = ApplyReferralCodeSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                referral_code = serializer.validated_data['referral_code']
                
                with transaction.atomic():
                    referrer = User.objects.get(referral_code=referral_code)
                    
                    # Create referral usage record
                    ReferralUsage.objects.create(
                        referrer=referrer,
                        referred_user=request.user,
                        is_rewarded=True
                    )
                    
                    # Add bonus to referrer's wallet (₹50)
                    referrer_wallet = referrer.wallet
                    referrer_bonus = Decimal('50.00')
                    WalletTransaction.objects.create(
                        wallet=referrer_wallet,
                        amount=referrer_bonus,
                        transaction_type='CREDIT',
                        status='SUCCESS',
                        description='Referral bonus for referring a user'
                    )
                    referrer_wallet.add_balance(referrer_bonus)
                    
                    # Add bonus to user's wallet (₹30)
                    user_wallet = request.user.wallet
                    user_bonus = Decimal('30.00')
                    WalletTransaction.objects.create(
                        wallet=user_wallet,
                        amount=user_bonus,
                        transaction_type='CREDIT',
                        status='SUCCESS',
                        description='Bonus for using referral code'
                    )
                    user_wallet.add_balance(user_bonus)
                    
                    return Response({
                        'message': 'Referral code applied successfully',
                        'bonus_earned': '30.00'
                    }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as exc:
            return self.handle_exception(exc)