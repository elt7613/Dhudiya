from rest_framework import serializers
from .models import Collection, Customer, RateStep, MarketMilkPrice, DairyInformation


class MarketMilkPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketMilkPrice
        fields = ['id', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'is_active']
        read_only_fields = ['is_active']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class CollectionListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Collection
        fields = [
            'id', 'collection_time', 'milk_type', 'customer_name',
            'collection_date', 'measured', 'liters', 'kg',
            'fat_percentage', 'fat_kg', 'clr', 'snf_percentage', 'snf_kg',
            'fat_rate', 'snf_rate', 'rate', 'amount'
        ]

class CollectionDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Collection
        fields = [
            'id', 'collection_time', 'milk_type', 'customer',
            'customer_name', 'collection_date', 'measured', 'liters', 'kg',
            'fat_percentage', 'fat_kg', 'clr', 'snf_percentage', 'snf_kg',
            'fat_rate', 'snf_rate', 'rate', 'amount',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['is_active', 'created_at', 'updated_at']

    def validate_customer(self, value):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("No request found in context")
        
        # Check if the customer exists and belongs to the current user
        if not Customer.objects.filter(id=value.id, author=request.user).exists():
            raise serializers.ValidationError(
                "Invalid customer. Please select a customer that belongs to your account."
            )
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class RateStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateStep
        fields = [
            'id', 'rate_type', 'milk_type', 
            'fat_from', 'fat_to', 'fat_rate',
            'snf_from', 'snf_to', 'snf_rate',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class DairyInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DairyInformation
        fields = ['id', 'dairy_name', 'dairy_address', 'rate_type', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data) 