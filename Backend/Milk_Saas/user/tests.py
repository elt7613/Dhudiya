from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import User, ReferralUsage
from wallet.models import Wallet, WalletTransaction
from decimal import Decimal
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
import json

User = get_user_model()

class BaseAPITest(APITestCase):
    """Base test class with common setup and teardown"""
    def setUp(self):
        cache.clear()  # Clear cache at the start of each test
        self.client = APIClient()

    def tearDown(self):
        cache.clear()  # Clear cache after each test

    def remove_authentication(self):
        """Helper method to remove authentication"""
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION='')

class UserModelTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.user_data = {
            'username': 'testuser',
            'phone_number': '9876543210',  # Remove +91 prefix for model creation
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test user creation with valid data"""
        self.assertEqual(self.user.username, self.user_data['username'])
        # The model adds +91 prefix to phone numbers
        self.assertEqual(self.user.phone_number, f"+91{self.user_data['phone_number']}")
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertIsNotNone(self.user.referral_code)
        self.assertEqual(len(self.user.referral_code), 5)

    def test_user_str_representation(self):
        """Test string representation of user"""
        expected_str = f"{self.user.username} ({self.user.phone_number})"
        self.assertEqual(str(self.user), expected_str)

    def test_wallet_creation(self):
        """Test wallet is automatically created for new user"""
        self.assertIsNotNone(self.user.wallet)
        self.assertEqual(self.user.wallet.balance, Decimal('0.00'))

    def test_unique_referral_code_generation(self):
        """Test unique referral code generation"""
        user2_data = {
            'username': 'testuser2',
            'phone_number': '9876543211',  # Remove +91 prefix
            'email': 'test2@example.com',
            'password': 'testpass123'
        }
        user2 = User.objects.create_user(**user2_data)
        self.assertNotEqual(self.user.referral_code, user2.referral_code)

    def test_soft_delete(self):
        """Test soft deletion of user"""
        self.user.soft_delete()
        self.assertFalse(self.user.is_active)
        self.assertFalse(User.objects.filter(username=self.user.username).exists())
        self.assertTrue(User.all_objects.filter(username=self.user.username).exists())

class UserRegistrationTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')
        
        # Create referrer for referral tests
        self.referrer = User.objects.create_user(
            username='referrer',
            phone_number='9876543210',
            email='referrer@example.com',
            password='testpass123'
        )

    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'phone_number': '9876543212',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'terms_accepted': True,
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Registration failed with response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=data['email']).exists())
        
        # Verify user can login
        login_data = {
            'login_field': data['username'],
            'password': data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_registration_with_referral(self):
        """Test user registration with referral code"""
        data = {
            'username': 'newuser',
            'phone_number': '9876543212',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'terms_accepted': True,
            'first_name': 'New',
            'last_name': 'User',
            'referral_code': self.referrer.referral_code
        }
        response = self.client.post(self.register_url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Registration with referral failed with response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=data['email']).exists())
        
        # Verify referral was applied
        new_user = User.objects.get(email=data['email'])
        referral_usage = ReferralUsage.objects.filter(
            referrer=self.referrer,
            referred_user=new_user
        ).first()
        self.assertIsNotNone(referral_usage, "No referral usage record found")
        
        # Verify wallet bonuses
        referrer_wallet = Wallet.objects.get(user=self.referrer)
        new_user_wallet = Wallet.objects.get(user=new_user)
        self.assertEqual(referrer_wallet.balance, Decimal('50.00'))
        self.assertEqual(new_user_wallet.balance, Decimal('30.00'))

    def test_invalid_registration_data(self):
        """Test registration with invalid data"""
        # Test missing required fields
        invalid_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'terms_accepted': True,
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        
        # Test invalid phone number
        invalid_data = {
            'username': 'testuser',
            'phone_number': '123',  # Invalid phone number
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'terms_accepted': True,
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
        
        # Test duplicate username
        # First create a user
        valid_data = {
            'username': 'testuser',
            'phone_number': '9876543212',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'terms_accepted': True,
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create another user with same username
        duplicate_data = valid_data.copy()
        duplicate_data['phone_number'] = '9876543213'  # Different phone
        duplicate_data['email'] = 'test2@example.com'  # Different email
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

class UserLoginTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.login_url = reverse('user-login')
        self.user_data = {
            'username': 'testuser',
            'phone_number': '9876543210',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        # Clear cache at the start of each test
        cache.clear()

    def test_login_with_username(self):
        """Test login with username"""
        cache.clear()  # Ensure clean cache state
        data = {
            'login_field': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_with_phone(self):
        """Test login with phone number"""
        cache.clear()  # Ensure clean cache state
        data = {
            'login_field': self.user_data['phone_number'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_failed_login_attempts(self):
        """Test failed login attempts and rate limiting"""
        # Clear cache and set up throttle key
        cache.clear()
        data = {
            'login_field': self.user_data['username'],
            'password': 'wrongpassword'
        }
        
        # Make 5 failed attempts to trigger lockout
        for i in range(5):
            response = self.client.post(self.login_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            # Ensure cache is updated
            cache_key = f"login_attempts_{data['login_field']}"
            self.assertIsNotNone(cache.get(cache_key))
        
        # Next attempt should be rate limited with exponential backoff
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('lockout_minutes', response.data)
        self.assertIn('error', response.data)
        self.assertIn('Too many failed attempts', response.data['error'])

class UserInfoTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.info_url = reverse('user-info')
        self.user_data = {
            'username': 'testuser',
            'phone_number': '9876543210',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_get_user_info(self):
        """Test getting authenticated user info"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_details']['username'], self.user.username)
        self.assertEqual(response.data['user_details']['phone_number'], self.user.phone_number)
        self.assertEqual(response.data['user_details']['email'], self.user.email)
        self.assertIn('wallet', response.data)
        self.assertEqual(response.data['wallet']['balance'], '0.00')

    def test_unauthenticated_access(self):
        """Test unauthenticated access to user info"""
        self.remove_authentication()
        response = self.client.get(self.info_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')

class ReferralTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.apply_referral_url = reverse('apply-referral')
        self.user_info_url = reverse('user-info')  # Use user-info endpoint instead
        
        # Create referrer
        self.referrer = User.objects.create_user(
            username='referrer',
            phone_number='9876543210',  # Remove +91 prefix
            email='referrer@example.com',
            password='testpass123'
        )
        
        # Create user who will use referral
        self.user = User.objects.create_user(
            username='testuser',
            phone_number='9876543211',  # Remove +91 prefix
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)

    def test_apply_valid_referral(self):
        """Test applying a valid referral code"""
        data = {'referral_code': self.referrer.referral_code}
        response = self.client.post(self.apply_referral_url, data, format='json')
        
        if response.status_code != status.HTTP_200_OK:
            print(f"Apply referral failed with response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bonus_earned', '0.00'), '30.00')
        
        # Verify referral bonuses
        referrer_wallet = Wallet.objects.get(user=self.referrer)
        user_wallet = Wallet.objects.get(user=self.user)
        
        self.assertEqual(referrer_wallet.balance, Decimal('50.00'))
        self.assertEqual(user_wallet.balance, Decimal('30.00'))

    def test_apply_invalid_referral(self):
        """Test applying an invalid referral code"""
        response = self.client.post(self.apply_referral_url, {'referral_code': 'INVALID123'})
        
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print(f"Unexpected response status {response.status_code} with data: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Print full response data for debugging
        print(f"Response data: {response.data}")
        
        # Extract error message from nested structure
        error_message = ''
        if isinstance(response.data, dict):
            # Check for nested error messages in referral_code field
            if 'referral_code' in response.data and isinstance(response.data['referral_code'], list):
                error_message = str(response.data['referral_code'][0])
            else:
                error_message = (
                    str(response.data.get('message', '')) or 
                    str(response.data.get('error', '')) or 
                    str(response.data.get('detail', ''))
                )
        elif isinstance(response.data, str):
            error_message = response.data
            
        error_message = error_message.lower()
        print(f"Error message extracted: {error_message}")
        
        # More flexible error message checking
        expected_phrases = ['invalid', 'not found', 'does not exist', 'incorrect', 'wrong', 'ensure', 'characters']
        matching_phrases = [phrase for phrase in expected_phrases if phrase in error_message]
        
        self.assertTrue(
            len(matching_phrases) > 0,
            f"Error message '{error_message}' does not contain any expected phrases: {expected_phrases}"
        )

    def test_apply_own_referral(self):
        """Test applying own referral code"""
        # Get user's referral code from user info
        response = self.client.get(self.user_info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        referral_code = response.data['user_details']['referral_code']
        self.assertIsNotNone(referral_code, "No referral code found in response")
        
        # Try to apply own referral
        response = self.client.post(self.apply_referral_url, {'referral_code': referral_code})
        
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print(f"Unexpected response status {response.status_code} with data: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Print full response data for debugging
        print(f"Response data: {response.data}")
        
        # Extract error message from nested structure
        error_message = ''
        if isinstance(response.data, dict):
            # Check for nested error messages in referral_code field
            if 'referral_code' in response.data and isinstance(response.data['referral_code'], list):
                error_message = str(response.data['referral_code'][0])
            else:
                error_message = (
                    str(response.data.get('message', '')) or 
                    str(response.data.get('error', '')) or 
                    str(response.data.get('detail', ''))
                )
        elif isinstance(response.data, str):
            error_message = response.data
            
        error_message = error_message.lower()
        print(f"Error message extracted: {error_message}")
        
        # More flexible error message checking
        expected_phrases = ['own', 'self', 'cannot use your own', 'same user', 'yourself']
        matching_phrases = [phrase for phrase in expected_phrases if phrase in error_message]
        
        self.assertTrue(
            len(matching_phrases) > 0,
            f"Error message '{error_message}' does not contain any expected phrases: {expected_phrases}"
        )

    def test_unauthenticated_referral_access(self):
        """Test applying referral code without authentication"""
        self.remove_authentication()
        data = {'referral_code': self.referrer.referral_code}
        response = self.client.post(self.apply_referral_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PasswordResetTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.forgot_password_url = reverse('forgot-password')
        self.reset_password_url = reverse('reset-password')
        self.user_data = {
            'username': 'testuser',
            'phone_number': '9876543210',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        # Clear cache at the start of each test
        cache.clear()

    def test_forgot_password_request(self):
        """Test initiating password reset"""
        data = {'email': self.user_data['email']}
        response = self.client.post(self.forgot_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)  # Verify email was sent
        self.assertIn('OTP has been sent', response.data['message'])

    def test_reset_password_with_otp(self):
        """Test resetting password with OTP"""
        # First request OTP
        response = self.client.post(self.forgot_password_url, {'email': self.user_data['email']})
        
        if response.status_code != status.HTTP_200_OK:
            print(f"OTP request failed with response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        
        # Get OTP from email
        email_content = mail.outbox[0].body
        print(f"Email content: {email_content}")
        
        # Extract OTP - looking for a 6-digit number
        import re
        otp_matches = re.findall(r'\b\d{6}\b', email_content)
        self.assertTrue(otp_matches, f"No 6-digit OTP found in email content: {email_content}")
        otp = otp_matches[0]
        
        # Reset password
        data = {
            'email': self.user_data['email'],
            'otp': otp,
            'new_password': 'newtestpass123'
        }
        response = self.client.post(self.reset_password_url, data, format='json')
        
        if response.status_code != status.HTTP_200_OK:
            print(f"Password reset failed with response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            'Password reset successful' in str(response.data.get('message', '')) or
            'successfully' in str(response.data.get('message', '')).lower()
        )
        
        # Verify new password works
        login_data = {
            'login_field': self.user_data['username'],
            'password': 'newtestpass123'
        }
        login_response = self.client.post(reverse('user-login'), login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_reset_password_rate_limiting(self):
        """Test rate limiting for password reset requests"""
        # Clear cache and set up throttle key
        cache.clear()
        data = {'email': self.user_data['email']}
        
        # Make 3 requests (limit is 3 per hour)
        for i in range(3):
            response = self.client.post(self.forgot_password_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Ensure cache is updated
            cache_key = f"pwd_reset_{data['email']}"
            self.assertIsNotNone(cache.get(cache_key))
        
        # Next request should be rate limited
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)
        self.assertIn('Too many password reset attempts', response.data['error'])
