from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from .models import Collection, Customer, RateChart, MarketMilkPrice
from .serializers import (
    CollectionListSerializer, 
    CollectionDetailSerializer,
    CustomerSerializer,
    RateChartSerializer,
    MarketMilkPriceSerializer
)
from .filters import CollectionFilter, RateChartFilter

class MarketMilkPriceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MarketMilkPriceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['price']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return MarketMilkPrice.objects.filter(author=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()
        return Response({'message': 'Market milk price deleted successfully'}, status=status.HTTP_200_OK)

class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone']

    def get_queryset(self):
        return Customer.objects.filter(author=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()
        return Response({'message': 'Customer deleted successfully'}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Customer deleted successfully'}, status=status.HTTP_200_OK)

class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['collection_time', 'milk_type', 'collection_date']
    search_fields = ['customer__name']
    ordering_fields = [
        'collection_date', 'created_at', 'liters', 'kg',
        'fat_percentage', 'fat_kg', 'snf_percentage', 'snf_kg',
        'rate', 'amount'
    ]
    ordering = ['-collection_date', '-created_at']
    filterset_class = CollectionFilter

    def get_queryset(self):
        queryset = Collection.objects.select_related(
            'customer', 'author'
        ).filter(author=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionDetailSerializer

    def perform_destroy(self, instance):
        instance.soft_delete()
        return Response({'message': 'Collection deleted successfully'}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Collection deleted successfully'}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RateChartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RateChartSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RateChartFilter
    ordering_fields = ['rate', 'fat_from', 'fat_to', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return RateChart.objects.filter(author=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()
        return Response(
            {'message': 'Rate chart deleted successfully'}, 
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Rate chart deleted successfully'}, status=status.HTTP_200_OK)
