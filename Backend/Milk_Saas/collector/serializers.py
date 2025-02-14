from rest_framework import serializers
from .models import Collection, Customer, RateChart, MarketMilkPrice


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
            'rate', 'amount'
        ]

class CollectionDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Collection
        fields = [
            'id', 'collection_time', 'milk_type', 'customer',
            'customer_name', 'collection_date', 'measured', 'liters', 'kg',
            'fat_percentage', 'fat_kg', 'clr', 'snf_percentage', 'snf_kg',
            'rate', 'amount',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class RateChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateChart
        fields = [
            'id', 'rate_type', 'milk_type', 
            'fat_from', 'fat_to', 'rate',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data) 