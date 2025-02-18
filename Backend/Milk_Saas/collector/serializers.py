from rest_framework import serializers
from django.db import transaction
from .models import Collection, Customer, MarketMilkPrice, DairyInformation

class BaseModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        abstract = True
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

class MarketMilkPriceSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = MarketMilkPrice
        fields = ['id', 'price', 'is_active', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

class CustomerSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Customer
        fields = ['id', 'name', 'phone', 'is_active']

    def validate_phone(self, value):
        if not value:
            return value
            
        # Remove any existing '+' or leading zeros
        cleaned_phone = value.lstrip('+0')
        
        # Check if the phone number contains only digits
        if not cleaned_phone.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
            
        # Check if the length is valid (10 digits for Indian numbers)
        if len(cleaned_phone) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
            
        return cleaned_phone  # Return cleaned number, model's save() will add +91

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

    @transaction.atomic
    def update(self, instance, validated_data):
        # Handle phone number update
        if 'phone' in validated_data:
            phone = validated_data['phone']
            if phone and not phone.startswith('+91'):
                # Remove any existing '+' or leading zeros
                cleaned_phone = phone.lstrip('+0')
                # Add +91 prefix
                validated_data['phone'] = f'+91{cleaned_phone}'

        return super().update(instance, validated_data)

class CollectionListSerializer(BaseModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Collection
        fields = [
            'id', 'collection_time', 'milk_type', 'customer_name',
            'collection_date', 'measured', 'liters', 'kg',
            'fat_percentage', 'fat_kg', 'clr', 'snf_percentage', 'snf_kg',
            'fat_rate', 'snf_rate', 'rate', 'amount',
            'base_snf_percentage'
        ]

class CollectionDetailSerializer(BaseModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Collection
        fields = [
            'id', 'collection_time', 'milk_type', 'customer',
            'customer_name', 'collection_date', 'measured', 'liters', 'kg',
            'fat_percentage', 'fat_kg', 'clr', 'snf_percentage', 'snf_kg',
            'fat_rate', 'snf_rate', 'rate', 'amount',
            'base_fat_percentage', 'base_snf_percentage',
            'created_at', 'updated_at', 'is_active'
        ]

    def validate(self, data):
        # Validate numeric fields
        numeric_fields = ['liters', 'kg', 'fat_percentage', 'fat_kg', 'clr', 
                         'snf_percentage', 'snf_kg', 'rate', 'amount']
        for field in numeric_fields:
            if field in data and data[field] <= 0:
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} must be greater than 0"})

        # Validate percentages
        percentage_fields = ['fat_percentage', 'snf_percentage']
        for field in percentage_fields:
            if field in data and data[field] > 100:
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} cannot be greater than 100"})

        return data

    def validate_customer(self, value):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("No request found in context")
        
        if not Customer.objects.filter(id=value.id, author=request.user, is_active=True).exists():
            raise serializers.ValidationError(
                "Invalid customer. Please select an active customer that belongs to your account."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class DairyInformationSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = DairyInformation
        fields = ['id', 'dairy_name', 'dairy_address', 'rate_type', 'is_active', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate required fields
        if not data.get('dairy_name'):
            raise serializers.ValidationError({"dairy_name": "Dairy name is required"})
        
        if not data.get('rate_type'):
            raise serializers.ValidationError({"rate_type": "Rate type is required"})
            
        # Validate rate_type choices
        valid_rate_types = [choice[0] for choice in DairyInformation.RATE_TYPE_CHOICES]
        if data.get('rate_type') and data['rate_type'] not in valid_rate_types:
            raise serializers.ValidationError({
                "rate_type": f"Invalid rate type. Must be one of: {', '.join(valid_rate_types)}"
            })
        
        return data

    def validate_dairy_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Dairy name cannot be empty")

        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("No request found in context")

        # Check for duplicate dairy names for the same user
        if DairyInformation.objects.filter(
            dairy_name__iexact=value.strip(),
            author=request.user,
            is_active=True
        ).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError("A dairy with this name already exists")
            
        return value.strip()

    def validate_dairy_address(self, value):
        if value:
            return value.strip()
        return value 