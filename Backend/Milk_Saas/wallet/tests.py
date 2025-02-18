from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch
import json
from django.utils import timezone
from datetime import timedelta

from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer, AddMoneySerializer

User = get_user_model()

class BaseTestCase(APITestCase):
    def setUp(self):
        # Create a unique test user for each test using a counter
        timestamp = timezone.now().strftime('%H%M%S')
        last_4_digits = timestamp[-4:]  # Take only the last 4 digits
        try:
            self.user = User.objects.create_user(
                username=f'testuser_{timestamp}',
                password='testpass123',
                phone_number=f'987654{last_4_digits}'  # This will be exactly 10 digits
            )
            self.client = APIClient()
            self.client.force_authenticate(user=self.user)
            
            # Get or update the wallet that was automatically created by the signal
            self.wallet = Wallet.objects.get(user=self.user)
            self.wallet.balance = Decimal('1000.00')
            self.wallet.save()
            
            # Create a test transaction
            self.transaction = WalletTransaction.objects.create(
                wallet=self.wallet,
                amount=Decimal('100.00'),
                transaction_type='CREDIT',
                status='SUCCESS',
                description='Test transaction'
            )
        except Exception as e:
            # Clean up if any creation fails
            self.tearDown()
            raise
        
    def tearDown(self):
        try:
            if hasattr(self, 'user'):
                # Delete all related objects first
                if hasattr(self, 'wallet'):
                    WalletTransaction.objects.filter(wallet=self.wallet).delete()
                    self.wallet.delete()
                
                # Delete user last
                self.user.delete()
                
                # Clear instance attributes
                if hasattr(self, 'wallet'):
                    delattr(self, 'wallet')
                delattr(self, 'user')
        except Exception as e:
            print(f"Error in tearDown: {e}")

class ModelTests(BaseTestCase):
    def test_wallet_model(self):
        """Test wallet model creation and methods"""
        # Create a new user and get their wallet
        new_user = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            phone_number='9876543210'
        )
        wallet = Wallet.objects.get(user=new_user)
        wallet.balance = Decimal('500.00')
        wallet.save()
        
        self.assertEqual(str(wallet), f"{new_user.username}'s Wallet - ₹500.00")
        self.assertTrue(wallet.is_active)
        self.assertEqual(wallet.balance, Decimal('500.00'))
        
        # Test credit method
        wallet.add_balance(Decimal('100.00'))
        self.assertEqual(wallet.balance, Decimal('600.00'))
        
        # Test debit method
        wallet.subtract_balance(Decimal('50.00'))
        self.assertEqual(wallet.balance, Decimal('550.00'))
        
        # Test insufficient balance
        with self.assertRaises(ValueError):
            wallet.subtract_balance(Decimal('1000.00'))

    def test_wallet_transaction_model(self):
        """Test wallet transaction model creation and validation"""
        # Test transaction creation
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='CREDIT',
            status='PENDING',
            description='Test credit transaction'
        )
        self.assertEqual(str(transaction), f"{self.user.username} - CREDIT - ₹50.00")
        
        # Test negative amount validation
        with self.assertRaises(ValueError):
            WalletTransaction.objects.create(
                wallet=self.wallet,
                amount=Decimal('-50.00'),
                transaction_type='CREDIT',
                status='PENDING'
            )
        
        # Test invalid transaction type
        with self.assertRaises(ValueError):
            WalletTransaction.objects.create(
                wallet=self.wallet,
                amount=Decimal('50.00'),
                transaction_type='INVALID',
                status='PENDING'
            )
        
        # Test invalid status
        with self.assertRaises(ValueError):
            WalletTransaction.objects.create(
                wallet=self.wallet,
                amount=Decimal('50.00'),
                transaction_type='CREDIT',
                status='INVALID'
            )

    def test_soft_deletion(self):
        """Test soft deletion functionality"""
        # Test wallet soft deletion
        self.wallet.soft_delete()
        self.assertFalse(Wallet.objects.filter(id=self.wallet.id).exists())
        self.assertTrue(Wallet.all_objects.filter(id=self.wallet.id).exists())
        
        # Test transaction soft deletion
        self.transaction.soft_delete()
        self.assertFalse(WalletTransaction.objects.filter(id=self.transaction.id).exists())
        self.assertTrue(WalletTransaction.all_objects.filter(id=self.transaction.id).exists())

class APITests(BaseTestCase):
    def test_wallet_list(self):
        """Test wallet list endpoint"""
        url = reverse('wallet-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['balance']), self.wallet.balance)

    def test_wallet_transaction_create(self):
        """Test transaction creation endpoint"""
        url = reverse('wallet-transaction-list')
        
        # Test credit transaction
        data = {
            'amount': '100.00',
            'transaction_type': 'credit',
            'description': 'Test credit'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['amount']), Decimal('100.00'))
        
        # Test debit transaction
        data = {
            'amount': '50.00',
            'transaction_type': 'debit',
            'description': 'Test debit'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['amount']), Decimal('50.00'))
        
        # Test insufficient balance
        data = {
            'amount': '2000.00',
            'transaction_type': 'debit',
            'description': 'Test insufficient'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient balance', response.data['error'])

    def test_wallet_transaction_list(self):
        """Test transaction list endpoint"""
        url = reverse('wallet-transaction-list')
        
        # Create multiple transactions
        WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('75.00'),
            transaction_type='CREDIT',
            status='SUCCESS'
        )
        WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('25.00'),
            transaction_type='DEBIT',
            status='SUCCESS'
        )
        
        # Test basic list
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # Including setup transaction
        
        # Test transaction type filter
        response = self.client.get(f"{url}?transaction_type=CREDIT")
        self.assertEqual(len(response.data['results']), 2)  # Two CREDIT transactions: one from setUp and one created in this test
        
        # Test status filter
        response = self.client.get(f"{url}?status=SUCCESS")
        self.assertEqual(len(response.data['results']), 3)  # All transactions have SUCCESS status
        
        # Test date range filter
        today = timezone.now().date()
        response = self.client.get(f"{url}?date_from={today}&date_to={today}")
        self.assertEqual(len(response.data['results']), 3)  # All transactions are created today

    def test_wallet_balance_update(self):
        """Test wallet balance update endpoint is not allowed"""
        url = reverse('wallet-detail', args=[self.wallet.id])
        
        # Test balance update - should not be allowed
        data = {'balance': '1500.00'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_transaction_status_update(self):
        """Test transaction status update endpoint is not allowed"""
        url = reverse('wallet-transaction-detail', args=[self.transaction.id])
        
        # Test status update - should not be allowed
        data = {'status': 'FAILED'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class SerializerTests(BaseTestCase):
    def test_wallet_serializer(self):
        """Test wallet serializer"""
        serializer = WalletSerializer(self.wallet)
        self.assertEqual(Decimal(serializer.data['balance']), self.wallet.balance)
        
        # Test validation
        data = {'balance': '-100.00'}
        serializer = WalletSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('balance', serializer.errors)

    def test_wallet_transaction_serializer(self):
        """Test wallet transaction serializer"""
        serializer = WalletTransactionSerializer(self.transaction)
        self.assertEqual(Decimal(serializer.data['amount']), self.transaction.amount)
        self.assertEqual(serializer.data['transaction_type'], self.transaction.transaction_type)
        
        # Test validation
        data = {
            'wallet': self.wallet.id,
            'amount': '-50.00',
            'transaction_type': 'credit',
            'status': 'pending'
        }
        serializer = WalletTransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
        
        # Test transaction type validation
        data['amount'] = '50.00'
        data['transaction_type'] = 'invalid'
        serializer = WalletTransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('transaction_type', serializer.errors)
        
        # Test status validation
        data['transaction_type'] = 'credit'
        data['status'] = 'invalid'
        serializer = WalletTransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

class WalletBonusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='+919876543210'
        )
        self.wallet = self.user.wallet

    def test_bonus_calculation(self):
        """Test bonus calculation for different amounts"""
        from wallet.views import calculate_bonus_amount

        # Test no bonus (amount < 500)
        amount = Decimal('400.00')
        bonus, description = calculate_bonus_amount(amount)
        self.assertEqual(bonus, Decimal('0'))
        self.assertIsNone(description)

        # Test 5% bonus (500 <= amount < 1000)
        amount = Decimal('500.00')
        bonus, description = calculate_bonus_amount(amount)
        self.assertEqual(bonus, Decimal('25.00'))
        self.assertIn('5% bonus', description)

        # Test 10% bonus (amount >= 1000)
        amount = Decimal('1000.00')
        bonus, description = calculate_bonus_amount(amount)
        self.assertEqual(bonus, Decimal('100.00'))
        self.assertIn('10% bonus', description)

