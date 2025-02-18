from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.db import transaction
from django.db.models import F
import razorpay
from decimal import Decimal
import logging
from rest_framework.pagination import PageNumberPagination

from .models import Wallet, WalletTransaction
from .serializers import (
    WalletSerializer, 
    WalletTransactionSerializer,
    AddMoneySerializer
)

# Configure logging
logger = logging.getLogger(__name__)

def calculate_bonus_amount(amount):
    """Calculate bonus amount based on the recharge amount."""
    amount = Decimal(str(amount))
    
    if amount >= Decimal('1000'):
        bonus_percentage = Decimal('0.10')  # 10% bonus
        bonus_description = "10% bonus on recharge above ₹1000"
    elif amount >= Decimal('500'):
        bonus_percentage = Decimal('0.05')  # 5% bonus
        bonus_description = "5% bonus on recharge between ₹500-₹999"
    else:
        return Decimal('0'), None
    
    bonus_amount = amount * bonus_percentage
    return bonus_amount, bonus_description

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user).order_by('-created_at')

    def get_object(self):
        return self.get_queryset().first()

    def list(self, request, *args, **kwargs):
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        wallet = self.get_object()
        try:
            new_balance = Decimal(request.data.get('balance', 0))
            wallet.set_balance(new_balance)
            return Response(self.get_serializer(wallet).data)
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def add_money(self, request):
        serializer = AddMoneySerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Invalid add_money request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']

        try:
            # Log Razorpay configuration
            logger.info(f"Initializing Razorpay client with key_id: {settings.RAZORPAY_KEY_ID[:5]}...")
            
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Prepare customer data with fallbacks
            customer_data = {
                'name': request.user.username,
                'email': getattr(request.user, 'email', ''),
                'contact': getattr(request.user, 'phone_number', '')
            }
            
            logger.info(f"Creating payment for user: {customer_data['name']}, amount: {amount}")

            # Create payment link with optimized data
            payment_link_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': 'INR',
                'accept_partial': False,
                'description': 'Wallet Recharge',
                'customer': customer_data,
                'notify': {
                    'sms': bool(customer_data['contact']),  # Only if phone number exists
                    'email': bool(customer_data['email'])   # Only if email exists
                },
                'reminder_enable': True,
            }

            # Log the payment link data (excluding sensitive info)
            safe_payment_data = {**payment_link_data}
            safe_payment_data['customer'] = {
                'name': customer_data['name'],
                'has_email': bool(customer_data['email']),
                'has_contact': bool(customer_data['contact'])
            }
            logger.info(f"Payment link data: {safe_payment_data}")

            payment_link = client.payment_link.create(payment_link_data)
            
            # Calculate bonus amount before the atomic block
            bonus_amount, bonus_description = calculate_bonus_amount(amount)
            
            # Use atomic transaction for data consistency
            with transaction.atomic():
                wallet = self.get_object()
                
                # Create the main transaction
                transaction_obj = WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='CREDIT',
                    status='PENDING',
                    razorpay_order_id=payment_link['id'],
                    description='Wallet Recharge'
                )
                
                # If there's a bonus, create a pending bonus transaction
                bonus_transaction = None
                if bonus_amount > 0:
                    bonus_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=bonus_amount,
                        transaction_type='CREDIT',
                        status='PENDING',
                        description=f'Pending {bonus_description}',
                        parent_transaction=transaction_obj
                    )

            # Optimize response data
            response_data = {
                'payment_link': payment_link['short_url'],
                'payment_link_id': payment_link['id'],
                'amount': amount,
                'transaction_id': transaction_obj.id,
                'status': 'PENDING'
            }

            if bonus_amount > 0:
                response_data.update({
                    'bonus_amount': bonus_amount,
                    'bonus_description': bonus_description,
                    'total_amount': amount + bonus_amount,
                    'bonus_transaction_id': bonus_transaction.id if bonus_transaction else None
                })
            elif amount < Decimal('500'):
                response_data['bonus_info'] = "Add ₹500 or more to get 5% bonus, ₹1000 or more to get 10% bonus!"

            logger.info(f"Payment link created successfully for user {request.user.id}")
            return Response(response_data, status=status.HTTP_200_OK)

        except razorpay.errors.BadRequestError as e:
            error_msg = str(e)
            logger.error(f"Razorpay BadRequestError: {error_msg}")
            logger.error(f"Request user data - Username: {request.user.username}, "
                        f"Has email: {bool(getattr(request.user, 'email', ''))}, "
                        f"Has phone: {bool(getattr(request.user, 'phone_number', ''))}")
            
            # Provide more specific error message based on the error
            if 'authentication' in error_msg.lower():
                return Response(
                    {'error': 'Razorpay authentication failed. Please check API keys.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'customer' in error_msg.lower():
                return Response(
                    {'error': 'Invalid customer details. Please update your profile with valid email and phone number.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': f'Payment request failed: {error_msg}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error in add_money: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        payment_link_id = request.data.get('payment_link_id')
        
        if not payment_link_id:
            logger.error("Payment link ID missing in verify_payment request")
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
            
            # Get transaction with optimized query
            try:
                wallet_transaction = WalletTransaction.objects.select_related('wallet').get(
                    razorpay_order_id=payment_link_id
                )
            except WalletTransaction.DoesNotExist:
                logger.error(f"Transaction not found for payment_link_id: {payment_link_id}")
                return Response(
                    {'error': 'Transaction not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if wallet_transaction.status == 'SUCCESS':
                return Response({
                    'message': 'Payment already verified',
                    'status': 'SUCCESS',
                    'amount_paid': payment_data['amount_paid'] / 100,
                    'wallet_balance': wallet_transaction.wallet.balance
                }, status=status.HTTP_200_OK)

            # If payment is successful
            if payment_data['status'] == 'paid':
                with transaction.atomic():
                    recharge_amount = Decimal(str(payment_data['amount_paid'] / 100))
                    
                    # Update main transaction atomically
                    wallet_transaction.status = 'SUCCESS'
                    wallet_transaction.razorpay_payment_id = payment_data['payments'][0]['payment_id']
                    wallet_transaction.save(update_fields=['status', 'razorpay_payment_id', 'updated_at'])

                    # Update wallet balance atomically
                    wallet = wallet_transaction.wallet
                    wallet.balance = F('balance') + recharge_amount
                    wallet.save(update_fields=['balance', 'updated_at'])
                    
                    # Refresh from db to get updated balance
                    wallet.refresh_from_db()
                    
                    # Check for and process any pending bonus transaction
                    bonus_transaction = WalletTransaction.objects.filter(
                        parent_transaction=wallet_transaction,
                        status='PENDING'
                    ).first()
                    
                    if bonus_transaction:
                        bonus_transaction.status = 'SUCCESS'
                        bonus_transaction.description = bonus_transaction.description.replace('Pending ', '')
                        bonus_transaction.save(update_fields=['status', 'description', 'updated_at'])
                        
                        wallet.balance = F('balance') + bonus_transaction.amount
                        wallet.save(update_fields=['balance', 'updated_at'])
                        wallet.refresh_from_db()

                response_data = {
                    'message': 'Payment successful',
                    'status': 'SUCCESS',
                    'amount_paid': recharge_amount,
                    'payment_method': payment_data['payments'][0]['method'],
                    'payment_id': payment_data['payments'][0]['payment_id'],
                    'wallet_balance': wallet.balance
                }
                
                if bonus_transaction:
                    response_data.update({
                        'bonus_amount': bonus_transaction.amount,
                        'bonus_description': bonus_transaction.description,
                        'total_credited': recharge_amount + bonus_transaction.amount
                    })
                
                logger.info(f"Payment verified successfully for transaction {wallet_transaction.id}")
                return Response(response_data, status=status.HTTP_200_OK)
            
            return Response({
                'message': 'Payment pending',
                'status': 'PENDING',
                'amount': payment_data['amount'] / 100
            }, status=status.HTTP_200_OK)

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay BadRequestError in verify_payment: {str(e)}")
            return Response(
                {'error': 'Invalid payment verification request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in verify_payment: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        try:
            wallet = self.get_object()
            # Optimize query with select_related
            transactions = (WalletTransaction.objects
                          .filter(wallet=wallet)
                          .select_related('wallet')
                          .order_by('-created_at'))
            
            # Paginate results for better performance
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = WalletTransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = WalletTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            return Response(
                {'error': 'An error occurred while fetching transactions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WalletTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = WalletTransaction.all_objects.filter(
            wallet__user=self.request.user,
            is_deleted=False
        ).select_related('wallet', 'wallet__user').order_by('-created_at')

        # Apply transaction type filter
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type.upper())

        # Apply status filter
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status.upper())

        # Apply date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from and date_to:
            queryset = queryset.filter(created_at__date__range=[date_from, date_to])

        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        wallet = Wallet.objects.get(user=request.user)
        data = request.data.copy()
        data['wallet'] = wallet.id
        data['transaction_type'] = data.get('transaction_type', '').upper()
        data['status'] = data.get('status', 'PENDING').upper()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            amount = Decimal(data['amount'])
            if data['transaction_type'] == 'DEBIT':
                wallet.subtract_balance(amount)
            else:
                wallet.add_balance(amount)

            transaction = serializer.save()
            return Response(self.get_serializer(transaction).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        transaction = self.get_object()
        data = request.data.copy()
        if 'status' in data:
            data['status'] = data['status'].upper()

        serializer = self.get_serializer(transaction, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
