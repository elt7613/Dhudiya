from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, datetime, timedelta
from rest_framework.test import APIRequestFactory
from django.db.models import Q
from .models import Customer, Collection, RateStep, MarketMilkPrice
from .serializers import (
    CustomerSerializer,
    CollectionListSerializer,
    CollectionDetailSerializer,
    RateStepSerializer,
    MarketMilkPriceSerializer
)

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            phone_number='9876543210'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            author=self.user
        )
        
        # Create test rate step
        self.rate_step = RateStep.objects.create(
            rate_type='rate per kg',
            milk_type='cow',
            fat_from=Decimal('3.0'),
            fat_to=Decimal('4.0'),
            fat_rate=Decimal('45.00'),
            snf_from=Decimal('8.0'),
            snf_to=Decimal('9.0'),
            snf_rate=Decimal('45.00'),
            author=self.user
        )
        
        # Create test market price
        self.market_price = MarketMilkPrice.objects.create(
            price=Decimal('45.00'),
            author=self.user
        )
        
        # Create test collection
        self.collection = Collection.objects.create(
            collection_time='morning',
            milk_type='cow',
            customer=self.customer,
            collection_date=date.today(),
            measured='liters',
            liters=Decimal('10.50'),
            kg=Decimal('10.80'),
            fat_percentage=Decimal('3.5'),
            fat_kg=Decimal('0.38'),
            clr=Decimal('28.5'),
            snf_percentage=Decimal('8.5'),
            snf_kg=Decimal('0.92'),
            fat_rate=Decimal('45.00'),
            snf_rate=Decimal('45.00'),
            rate=Decimal('45.00'),
            amount=Decimal('486.00'),
            author=self.user
        )

    def test_customer_str(self):
        self.assertEqual(str(self.customer), 'Test Customer')

    def test_collection_str(self):
        expected = f"{self.customer} - {self.collection.collection_date} {self.collection.collection_time}"
        self.assertEqual(str(self.collection), expected)

    def test_rate_step_str(self):
        self.assertEqual(str(self.rate_step), "cow - rate per kg")

    def test_market_milk_price_str(self):
        self.assertEqual(str(self.market_price), "45.00")

    def test_soft_delete(self):
        # Test soft delete for all models
        self.customer.soft_delete()
        self.assertFalse(Customer.objects.filter(id=self.customer.id).exists())
        self.assertTrue(Customer.all_objects.filter(id=self.customer.id).exists())

        self.collection.soft_delete()
        self.assertFalse(Collection.objects.filter(id=self.collection.id).exists())
        self.assertTrue(Collection.all_objects.filter(id=self.collection.id).exists())

        self.rate_step.soft_delete()
        self.assertFalse(RateStep.objects.filter(id=self.rate_step.id).exists())
        self.assertTrue(RateStep.all_objects.filter(id=self.rate_step.id).exists())

        self.market_price.soft_delete()
        self.assertFalse(MarketMilkPrice.objects.filter(id=self.market_price.id).exists())
        self.assertTrue(MarketMilkPrice.all_objects.filter(id=self.market_price.id).exists())

class APITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            phone_number='9876543210'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            author=self.user
        )
        
        self.rate_step = RateStep.objects.create(
            rate_type='rate per kg',
            milk_type='cow',
            fat_from=Decimal('3.0'),
            fat_to=Decimal('4.0'),
            fat_rate=Decimal('45.00'),
            snf_from=Decimal('8.0'),
            snf_to=Decimal('9.0'),
            snf_rate=Decimal('45.00'),
            author=self.user
        )
        
        self.market_price = MarketMilkPrice.objects.create(
            price=Decimal('45.00'),
            author=self.user
        )
        
        self.collection = Collection.objects.create(
            collection_time='morning',
            milk_type='cow',
            customer=self.customer,
            collection_date=date.today(),
            measured='liters',
            liters=Decimal('10.50'),
            kg=Decimal('10.80'),
            fat_percentage=Decimal('3.5'),
            fat_kg=Decimal('0.38'),
            clr=Decimal('28.5'),
            snf_percentage=Decimal('8.5'),
            snf_kg=Decimal('0.92'),
            fat_rate=Decimal('45.00'),
            snf_rate=Decimal('45.00'),
            rate=Decimal('45.00'),
            amount=Decimal('486.00'),
            author=self.user
        )

    def test_customer_list(self):
        url = reverse('customer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_customer_create(self):
        url = reverse('customer-list')
        data = {
            'name': 'New Customer',
            'phone': '9876543210'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2)

    def test_collection_list(self):
        url = reverse('collection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_collection_create(self):
        url = reverse('collection-list')
        data = {
            'collection_time': 'evening',
            'milk_type': 'cow',
            'customer': self.customer.id,
            'collection_date': date.today().isoformat(),
            'measured': 'liters',
            'liters': '11.50',
            'kg': '11.80',
            'fat_percentage': '3.6',
            'fat_kg': '0.38',
            'clr': '28.6',
            'snf_percentage': '8.6',
            'snf_kg': '0.92',
            'fat_rate': '45.00',
            'snf_rate': '45.00',
            'rate': '45.00',
            'amount': '531.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Collection.objects.count(), 2)

    def test_rate_step_list(self):
        url = reverse('rate-step-list')
        response = self.client.get(url)
        if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            print("Response data:", response.data)  # Debug info
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, (dict, list)))
        if isinstance(response.data, dict):
            self.assertTrue('results' in response.data)
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_rate_step_create(self):
        url = reverse('rate-step-list')
        data = {
            'rate_type': 'rate per kg',
            'milk_type': 'buffalo',
            'fat_from': '4.0',
            'fat_to': '5.0',
            'fat_rate': '50.00',
            'snf_from': '9.0',
            'snf_to': '10.0',
            'snf_rate': '50.00'
        }
        response = self.client.post(url, data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Response data:", response.data)  # Debug info
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RateStep.objects.count(), 2)

    def test_market_price_list(self):
        url = reverse('market-milk-price-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_market_price_create(self):
        url = reverse('market-milk-price-list')
        data = {
            'price': '46.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MarketMilkPrice.objects.count(), 2)

    def test_collection_filters(self):
        url = reverse('collection-list')
        
        # Test date filter
        response = self.client.get(url, {
            'date_from': date.today().isoformat(),
            'date_to': date.today().isoformat()
        })
        self.assertEqual(len(response.data['results']), 1)
        
        # Test milk type filter
        response = self.client.get(url, {'milk_type': 'cow'})
        self.assertEqual(len(response.data['results']), 1)
        
        # Test customer filter
        response = self.client.get(url, {'customer': self.customer.id})
        self.assertEqual(len(response.data['results']), 1)

    def test_rate_step_filters(self):
        url = reverse('rate-step-list')
        
        # Test milk type filter
        response = self.client.get(url, {'milk_type': 'cow'})
        if not isinstance(response.data, (dict, list)):
            print("Response data:", response.data)  # Debug info
        self.assertTrue(isinstance(response.data, (dict, list)))
        if isinstance(response.data, dict):
            self.assertTrue('results' in response.data)
            count = len(response.data['results'])
        else:
            count = len(response.data)
        self.assertEqual(count, 1)
        
        # Test rate range filter
        response = self.client.get(url, {
            'min_fat_rate': '40.00',
            'max_fat_rate': '50.00'
        })
        self.assertTrue(isinstance(response.data, (dict, list)))
        if isinstance(response.data, dict):
            self.assertTrue('results' in response.data)
            count = len(response.data['results'])
        else:
            count = len(response.data)
        self.assertEqual(count, 1)

    def test_authentication_required(self):
        # Test without authentication
        self.client.force_authenticate(user=None)
        
        urls = [
            reverse('customer-list'),
            reverse('collection-list'),
            reverse('rate-step-list'),
            reverse('market-milk-price-list')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_specific_data(self):
        # Create another user and their data
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            phone_number='5555555555'
        )
        
        other_customer = Customer.objects.create(
            name='Other Customer',
            phone='5555555555',
            author=other_user
        )
        
        # Test that first user can't see other user's data
        url = reverse('customer-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Customer')

    def test_generate_invoice(self):
        # First ensure we have some collection data
        Collection.objects.create(
            collection_time='morning',
            milk_type='cow',
            customer=self.customer,
            collection_date=date.today(),
            measured='liters',
            liters=Decimal('10.50'),
            kg=Decimal('10.80'),
            fat_percentage=Decimal('3.5'),
            fat_kg=Decimal('0.38'),
            clr=Decimal('28.5'),
            snf_percentage=Decimal('8.5'),
            snf_kg=Decimal('0.92'),
            fat_rate=Decimal('45.00'),
            snf_rate=Decimal('45.00'),
            rate=Decimal('45.00'),
            amount=Decimal('486.00'),
            author=self.user
        )

        url = reverse('collection-generate-invoice')
        params = {
            'start_date': date.today().isoformat(),
            'end_date': date.today().isoformat(),
            'report_type': 'purchase_report',
            'customer': self.customer.id,
            'collection_time': 'morning',
            'milk_type': 'cow'
        }
        response = self.client.get(url, params)
        if response.status_code != status.HTTP_200_OK:
            print("Response data:", response.data)  # Debug info
            print("Request params:", params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

class SerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            phone_number='9876543210'
        )
        
        self.customer_data = {
            'name': 'Test Customer',
            'phone': '1234567890'
        }
        
        self.collection_data = {
            'collection_time': 'morning',
            'milk_type': 'cow',
            'collection_date': date.today(),
            'measured': 'liters',
            'liters': Decimal('10.50'),
            'kg': Decimal('10.80'),
            'fat_percentage': Decimal('3.5'),
            'fat_kg': Decimal('0.38'),
            'clr': Decimal('28.5'),
            'snf_percentage': Decimal('8.5'),
            'snf_kg': Decimal('0.92'),
            'fat_rate': Decimal('45.00'),
            'snf_rate': Decimal('45.00'),
            'rate': Decimal('45.00'),
            'amount': Decimal('486.00')
        }

    def test_customer_serializer(self):
        serializer = CustomerSerializer(data=self.customer_data)
        self.assertTrue(serializer.is_valid())

    def test_collection_serializer(self):
        # Create required customer first
        customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            author=self.user
        )
        
        data = self.collection_data.copy()
        data['customer'] = customer.id
        data['author'] = self.user.id
        
        request = self.factory.post('/fake-url/')
        request.user = self.user
        
        serializer = CollectionDetailSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
