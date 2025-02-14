from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

User = get_user_model()

class UserModelTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'phone_number': '+919876543210',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """Test creating a new user"""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.phone_number, self.user_data['phone_number'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_user_str_method(self):
        """Test the string representation of user"""
        self.assertEqual(str(self.user), self.user.username)

class UserAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'phone_number': '+919876543210',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        cache.clear()  # Clear cache before each test

    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data['username'])

    def test_duplicate_username_registration(self):
        """Test registration with duplicate username"""
        # Create first user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to create user with same username
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_login_with_username(self):
        """Test login with username"""
        # Create user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Login
        login_data = {
            'login_field': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_with_phone(self):
        """Test login with phone number"""
        # Create user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Login with phone
        login_data = {
            'login_field': self.user_data['phone_number'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_with_wrong_password(self):
        """Test login with wrong password"""
        # Create user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try login with wrong password
        login_data = {
            'login_field': self.user_data['username'],
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_attempt_limit(self):
        """Test login attempt limit"""
        # Create user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try multiple failed login attempts
        login_data = {
            'login_field': self.user_data['username'],
            'password': 'wrongpassword'
        }
        
        # Make 5 failed attempts
        for _ in range(5):
            response = self.client.post(self.login_url, login_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 6th attempt should be blocked
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_registration_with_invalid_phone(self):
        """Test registration with invalid phone number"""
        invalid_user_data = self.user_data.copy()
        invalid_user_data['phone_number'] = '123'  # Invalid format
        
        response = self.client.post(self.register_url, invalid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_registration_without_required_fields(self):
        """Test registration without required fields"""
        invalid_data = {
            'username': 'testuser'
            # Missing required fields
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting(self):
        """Test rate limiting on registration endpoint"""
        # Make multiple requests quickly
        for _ in range(21):  # Our limit is 20 per minute
            response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            phone_number='+919876543210',
            password='testpass123'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)

    def test_authentication_with_valid_token(self):
        """Test authentication with valid token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        # Add a protected endpoint test here if you have one
        # response = self.client.get(reverse('protected-endpoint'))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authentication_without_token(self):
        """Test authentication without token"""
        # Add a protected endpoint test here if you have one
        # response = self.client.get(reverse('protected-endpoint'))
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_with_invalid_token(self):
        """Test authentication with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        # Add a protected endpoint test here if you have one
        # response = self.client.get(reverse('protected-endpoint'))
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
