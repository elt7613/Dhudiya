from rest_framework import serializers
from .models import Wallet, WalletTransaction
from decimal import Decimal

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['balance', 'created_at', 'updated_at']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'razorpay_order_id',
                 'razorpay_payment_id', 'description', 
                 'created_at', 'updated_at']
        read_only_fields = ['razorpay_order_id', 'razorpay_payment_id', 
                           'status', 'created_at', 'updated_at']

class AddMoneySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1.00')) 