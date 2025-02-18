from rest_framework import serializers
from decimal import Decimal
from django.core.validators import MinValueValidator

from .models import Wallet, WalletTransaction

class WalletSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        model = Wallet
        fields = ['id', 'username', 'balance', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value

class WalletTransactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='wallet.user.username', read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    transaction_type = serializers.ChoiceField(choices=WalletTransaction.TRANSACTION_TYPE_CHOICES)
    status = serializers.ChoiceField(choices=WalletTransaction.TRANSACTION_STATUS_CHOICES)

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'username', 'wallet', 'amount', 'transaction_type', 
            'status', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def validate_transaction_type(self, value):
        if value.upper() not in dict(WalletTransaction.TRANSACTION_TYPE_CHOICES):
            raise serializers.ValidationError("Invalid transaction type")
        return value.upper()

    def validate_status(self, value):
        if value.upper() not in dict(WalletTransaction.TRANSACTION_STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status")
        return value.upper()

class AddMoneySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value 