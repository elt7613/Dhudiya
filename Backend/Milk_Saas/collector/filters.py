from django_filters import rest_framework as filters
from .models import Collection, RateStep

class RateStepFilter(filters.FilterSet):
    min_rate = filters.NumberFilter(field_name='rate', lookup_expr='gte')
    max_rate = filters.NumberFilter(field_name='rate', lookup_expr='lte')
    min_fat = filters.NumberFilter(field_name='fat_from', lookup_expr='gte')
    max_fat = filters.NumberFilter(field_name='fat_to', lookup_expr='lte')

    class Meta:
        model = RateStep
        fields = {
            'milk_type': ['exact'],
            'rate_type': ['exact'],
            'is_active': ['exact'],
        }

class CollectionFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name='collection_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='collection_date', lookup_expr='lte')
    min_rate = filters.NumberFilter(field_name='rate', lookup_expr='gte')
    max_rate = filters.NumberFilter(field_name='rate', lookup_expr='lte')
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = Collection
        fields = {
            'collection_time': ['exact'],
            'milk_type': ['exact'],
            'customer': ['exact'],
            'measured': ['exact'],
            'liters': ['gte', 'lte'],
            'kg': ['gte', 'lte'],
            'fat_percentage': ['gte', 'lte'],
            'fat_kg': ['gte', 'lte'],
            'clr': ['gte', 'lte'],
            'snf_percentage': ['gte', 'lte'],
            'snf_kg': ['gte', 'lte'],
            'fat_rate': ['exact'],
            'snf_rate': ['exact'],
        } 