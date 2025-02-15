from django.shortcuts import render
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
import razorpay
import hmac
import hashlib

from .models import Wallet, WalletTransaction
from .serializers import (
    WalletSerializer, 
    WalletTransactionSerializer,
    AddMoneySerializer
)

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    @action(detail=False, methods=['post'])
    def add_money(self, request):
        serializer = AddMoneySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Create payment link
            payment_link_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': 'INR',
                'accept_partial': False,
                'description': 'Wallet Recharge',
                'customer': {
                    'name': request.user.username,
                    'email': request.user.email,
                    'contact': request.user.phone_number
                },
                'notify': {
                    'sms': True,
                    'email': True
                },
                'reminder_enable': True,
            }

            # Create payment link
            payment_link = client.payment_link.create(payment_link_data)

            # Create wallet transaction
            wallet = self.get_object()
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='CREDIT',
                status='PENDING',
                razorpay_order_id=payment_link['id'],
                description='Wallet Recharge'
            )

            # Return only necessary data
            response_data = {
                'payment_link': payment_link['short_url'],
                'payment_link_id': payment_link['id'],
                'amount': amount,
                'transaction_id': transaction.id,
                'status': 'PENDING'
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        payment_link_id = request.data.get('payment_link_id')
        
        if not payment_link_id:
            return Response(
                {'error': 'Payment link ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Fetch payment link status
            payment_data = client.payment_link.fetch(payment_link_id)
            
            # Get transaction
            wallet_transaction = WalletTransaction.objects.select_related('wallet').get(
                razorpay_order_id=payment_link_id
            )
            
            if wallet_transaction.status == 'SUCCESS':
                return Response({
                    'message': 'Payment already verified',
                    'status': 'SUCCESS',
                    'amount_paid': payment_data['amount_paid'] / 100,  # Convert from paise to rupees
                    'wallet_balance': wallet_transaction.wallet.balance
                }, status=status.HTTP_200_OK)

            # If payment is successful
            if payment_data['status'] == 'paid':
                with transaction.atomic():
                    # Update transaction with payment details
                    wallet_transaction.status = 'SUCCESS'
                    wallet_transaction.razorpay_payment_id = payment_data['payments'][0]['payment_id']
                    wallet_transaction.save()

                    # Update wallet balance
                    wallet = wallet_transaction.wallet
                    wallet.balance += wallet_transaction.amount
                    wallet.save()

                return Response({
                    'message': 'Payment successful',
                    'status': 'SUCCESS',
                    'amount_paid': payment_data['amount_paid'] / 100,
                    'payment_method': payment_data['payments'][0]['method'],
                    'payment_id': payment_data['payments'][0]['payment_id'],
                    'wallet_balance': wallet.balance
                }, status=status.HTTP_200_OK)
            
            # If payment is pending/created
            return Response({
                'message': 'Payment pending',
                'status': 'PENDING',
                'amount': payment_data['amount'] / 100  # Convert from paise to rupees
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        wallet = self.get_object()
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
