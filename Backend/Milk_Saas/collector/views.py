from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch, Sum, Avg, F, Min, Max, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from .models import Collection, Customer, MarketMilkPrice, DairyInformation
from .serializers import (
    CollectionListSerializer, 
    CollectionDetailSerializer,
    CustomerSerializer,
    MarketMilkPriceSerializer,
    DairyInformationSerializer
)
from .filters import CollectionFilter
from wallet.models import Wallet

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user, is_active=True)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.soft_delete()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    'message': f'{instance.__class__.__name__} deleted successfully',
                    'id': instance.id
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': f'Failed to delete {instance.__class__.__name__}.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_exception(self, exc):
        if isinstance(exc, (ValidationError, DRFValidationError)):
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return super().handle_exception(exc)

class MarketMilkPriceViewSet(BaseViewSet):
    queryset = MarketMilkPrice.objects.all()
    serializer_class = MarketMilkPriceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['price']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        # Get only the most recent active milk price
        milk_price = MarketMilkPrice.objects.filter(
            author=request.user,
            is_active=True
        ).order_by('-created_at').first()

        if milk_price:
            serializer = self.get_serializer(milk_price)
            return Response(serializer.data)
        return Response(
            {
                'detail': 'No milk price found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    def create(self, request, *args, **kwargs):
        try:
            # Soft delete any existing active milk price
            existing_price = MarketMilkPrice.objects.filter(
                author=request.user,
                is_active=True
            ).first()
            
            if existing_price:
                existing_price.soft_delete()

            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': 'Failed to create milk price. Please check your input.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': 'Failed to update milk price. Please check your input.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class DairyInformationViewSet(BaseViewSet):
    queryset = DairyInformation.objects.all()
    serializer_class = DairyInformationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dairy_name']
    ordering_fields = ['dairy_name', 'rate_type', 'created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        # Get only the most recent active dairy information
        dairy_info = DairyInformation.objects.filter(
            author=request.user,
            is_active=True
        ).order_by('-created_at').first()

        if dairy_info:
            serializer = self.get_serializer(dairy_info)
            return Response(serializer.data)
        return Response(
            {
                'detail': 'No dairy information found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    def create(self, request, *args, **kwargs):
        try:
            # Soft delete any existing active dairy information
            existing_dairy = DairyInformation.objects.filter(
                author=request.user,
                is_active=True
            ).first()
            
            if existing_dairy:
                existing_dairy.soft_delete()

            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': 'Failed to create dairy information. Please check your input.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': 'Failed to update dairy information. Please check your input.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class CustomerViewSet(BaseViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone']

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {
                    'error': str(e),
                    'detail': 'Failed to update customer. Please check your input.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_update(self, serializer):
        serializer.save()

class CollectionViewSet(BaseViewSet):
    queryset = Collection.objects.select_related('customer', 'author')
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

    def get_serializer_class(self):
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionDetailSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Check if this is first collection for this customer today
        collection_date = request.data.get('collection_date')
        customer_id = request.data.get('customer')
        base_snf_percentage = Decimal(str(request.data.get('base_snf_percentage', '9.0')))
        
        # Validate base_snf_percentage range
        if base_snf_percentage < Decimal('9.0') or base_snf_percentage > Decimal('9.5'):
            return Response(
                {'error': 'Base SNF percentage must be between 9.0 and 9.5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        today_collections = Collection.objects.filter(
            author=request.user,
            customer_id=customer_id,
            collection_date=collection_date,
            is_active=True
        )
        
        if not today_collections.exists():
            # This will be first collection for this customer today
            try:
                wallet = Wallet.objects.get(user=request.user)
                
                # Determine required balance based on base_snf_percentage
                default_snf = Decimal('9.0')
                required_balance = Decimal('5.00') if base_snf_percentage != default_snf else Decimal('2.00')
                
                if wallet.balance < required_balance:
                    return Response(
                        {
                            'error': 'Insufficient wallet balance. Please add money to your wallet to create new collections.',
                            'required_balance': str(required_balance),
                            'current_balance': str(wallet.balance),
                            'message': 'Higher balance required due to SNF adjustment' if required_balance == Decimal('5.00') else None
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Wallet.DoesNotExist:
                return Response(
                    {'error': 'No wallet found. Please contact support.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _generate_purchase_report(self, collections, doc, styles):
        """Generate the purchase report section with pagination support"""
        elements = []
        
        dairy_info = DairyInformation.objects.filter(author=self.request.user, is_active=True).first()
        dairy_name = dairy_info.dairy_name if dairy_info else self.request.user.username
        elements.append(Paragraph(f'<u>{dairy_name}</u>', styles['DairyName']))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph('PURCHASE REPORT', styles['ReportTitle']))
        
        start_date = collections.aggregate(min_date=Min('collection_date'))['min_date']
        end_date = collections.aggregate(max_date=Max('collection_date'))['max_date']
        
        elements.append(Paragraph(
            f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        daily_data = []
        header = ['DATE', 'WEIGHT (KG)', 'FAT %', 'FAT KG.', 'SNF %', 'SNF KG.', 'PUR.AMT', 'AMOUNT RS.']
        
        # Initialize grand totals
        grand_totals = {
            'total_kg': 0,
            'total_fat_kg': 0,
            'total_snf_kg': 0,
            'total_amount': 0,
            'purchase_amount': 0,
            'fat_percentage_sum': 0,
            'snf_percentage_sum': 0,
            'count': 0
        }
        
        for date in collections.values('collection_date').distinct().order_by('collection_date'):
            date_collections = collections.filter(collection_date=date['collection_date'])
            daily_totals = date_collections.aggregate(
                total_kg=Sum('kg'),
                total_fat_kg=Sum('fat_kg'),
                total_snf_kg=Sum('snf_kg'),
                total_amount=Sum('amount'),
                avg_fat_percentage=Avg('fat_percentage'),
                avg_snf_percentage=Avg('snf_percentage')
            )
            
            purchase_amount = daily_totals['total_amount']
            final_amount = int(purchase_amount * Decimal('0.999'))
            
            # Update grand totals
            grand_totals['total_kg'] += daily_totals['total_kg']
            grand_totals['total_fat_kg'] += daily_totals['total_fat_kg']
            grand_totals['total_snf_kg'] += daily_totals['total_snf_kg']
            grand_totals['purchase_amount'] += purchase_amount
            grand_totals['total_amount'] += final_amount
            grand_totals['fat_percentage_sum'] += daily_totals['avg_fat_percentage']
            grand_totals['snf_percentage_sum'] += daily_totals['avg_snf_percentage']
            grand_totals['count'] += 1
            
            daily_data.append([
                date['collection_date'].strftime('%d/%m/%Y'),
                f"{daily_totals['total_kg']:.2f}",
                f"{daily_totals['avg_fat_percentage']:.2f}",
                f"{daily_totals['total_fat_kg']:.3f}",
                f"{daily_totals['avg_snf_percentage']:.2f}",
                f"{daily_totals['total_snf_kg']:.3f}",
                f"{purchase_amount:.2f}",
                f"{final_amount}"
            ])

        rows_per_page = 25
        total_rows = len(daily_data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        col_widths = [
            doc.width * 0.13,  # DATE
            doc.width * 0.12, # WEIGHT
            doc.width * 0.12, # FAT %
            doc.width * 0.12, # FAT KG
            doc.width * 0.12, # SNF %
            doc.width * 0.12, # SNF KG
            doc.width * 0.13, # PUR.AMT
            doc.width * 0.14  # AMOUNT
        ]

        # Process each page
        for page_num in range(total_pages):
            start_idx = page_num * rows_per_page
            end_idx = min((page_num + 1) * rows_per_page, total_rows)
            
            page_data = daily_data[start_idx:end_idx]
            
            if page_num == total_pages - 1:
                avg_fat = grand_totals['fat_percentage_sum'] / grand_totals['count'] if grand_totals['count'] > 0 else 0
                avg_snf = grand_totals['snf_percentage_sum'] / grand_totals['count'] if grand_totals['count'] > 0 else 0
                page_data.append([
                    'TOTAL:',
                    f"{grand_totals['total_kg']:.2f}",
                    f"{avg_fat:.2f}",
                    f"{grand_totals['total_fat_kg']:.3f}",
                    f"{avg_snf:.2f}",
                    f"{grand_totals['total_snf_kg']:.3f}",
                    f"{grand_totals['purchase_amount']:.2f}",
                    f"{int(grand_totals['total_amount'])}"
                ])

            table = Table([header] + page_data, colWidths=col_widths)
            
            table_style = [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align dates
                ('ALIGN', (-2, 1), (-2, -1), 'RIGHT'),  # Right align purchase amount
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),  # Right align final amount
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]
            
            if page_num == total_pages - 1:
                table_style.extend([
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
                ])
            
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f'Page {page_num + 1} of {total_pages}',
                styles['PageNumber']
            ))
            
            if page_num < total_pages - 1:
                elements.append(PageBreak())
        
        elements.append(PageBreak())
        return elements

    def _generate_milk_purchase_summary(self, collections, doc, styles):
        """Generate the milk purchase summary section with pagination support"""
        elements = []
        
        elements.append(PageBreak())
        
        dairy_info = DairyInformation.objects.filter(author=self.request.user, is_active=True).first()
        dairy_name = dairy_info.dairy_name if dairy_info else self.request.user.username
        elements.append(Paragraph(f'<u>{dairy_name}</u>', styles['DairyName']))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph('MILK PURCHASE SUMMARY', styles['ReportTitle']))
        
        start_date = collections.aggregate(min_date=Min('collection_date'))['min_date']
        end_date = collections.aggregate(max_date=Max('collection_date'))['max_date']
        
        elements.append(Paragraph(
            f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        customer_data = []
        header = ['PARTY NAME', 'PHONE', 'WEIGHT', 'FAT %', 'FAT Kg.', 'SNF %', 'SNF Kg.', 'PUR.AMT', 'TOT. AMT.']
        
        # Initialize grand totals
        grand_totals = {
            'total_weight': 0,
            'total_fat_kg': 0,
            'total_snf_kg': 0,
            'purchase_amount': 0,
            'total_amount': 0,
            'fat_percentage_sum': 0,
            'snf_percentage_sum': 0,
            'customer_count': 0
        }
        
        customers = Customer.objects.filter(collection__in=collections).distinct()
        
        for customer in customers:
            customer_collections = collections.filter(customer=customer)
            customer_totals = customer_collections.aggregate(
                total_weight=Sum('kg'),
                total_fat_kg=Sum('fat_kg'),
                total_snf_kg=Sum('snf_kg'),
                total_amount=Sum('amount'),
                avg_fat_percentage=Avg('fat_percentage'),
                avg_snf_percentage=Avg('snf_percentage')
            )
            
            purchase_amount = customer_totals['total_amount']
            final_amount = int(purchase_amount * Decimal('0.999'))
            
            # Update grand totals
            grand_totals['total_weight'] += customer_totals['total_weight']
            grand_totals['total_fat_kg'] += customer_totals['total_fat_kg']
            grand_totals['total_snf_kg'] += customer_totals['total_snf_kg']
            grand_totals['purchase_amount'] += purchase_amount
            grand_totals['total_amount'] += final_amount
            grand_totals['fat_percentage_sum'] += customer_totals['avg_fat_percentage']
            grand_totals['snf_percentage_sum'] += customer_totals['avg_snf_percentage']
            grand_totals['customer_count'] += 1
            
            customer_data.append([
                f"{customer.id}-{customer.name}",
                customer.phone or '-',
                f"{customer_totals['total_weight']:.2f}",
                f"{customer_totals['avg_fat_percentage']:.2f}",
                f"{customer_totals['total_fat_kg']:.3f}",
                f"{customer_totals['avg_snf_percentage']:.2f}",
                f"{customer_totals['total_snf_kg']:.3f}",
                f"{purchase_amount:.2f}",
                f"{final_amount}"
            ])

        rows_per_page = 35
        total_rows = len(customer_data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        col_widths = [
            doc.width * 0.15,  # PARTY NAME
            doc.width * 0.11,  # PHONE
            doc.width * 0.10,  # WEIGHT
            doc.width * 0.09,  # FAT %
            doc.width * 0.11,  # FAT KG
            doc.width * 0.09,  # SNF %
            doc.width * 0.11,  # SNF KG
            doc.width * 0.12,  # PUR.AMT
            doc.width * 0.12   # TOT. AMT.
        ]

        # Process each page
        for page_num in range(total_pages):
            if page_num > 0:
                elements.append(PageBreak())
                elements.append(Paragraph(f'<u>{dairy_name}</u>', styles['DairyName']))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph('MILK PURCHASE SUMMARY', styles['ReportTitle']))
                elements.append(Paragraph(
                    f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
                    styles['DateRange']
                ))
                elements.append(Spacer(1, 8))
            
            start_idx = page_num * rows_per_page
            end_idx = min((page_num + 1) * rows_per_page, total_rows)
            
            page_data = customer_data[start_idx:end_idx]
            
            if page_num == total_pages - 1:
                avg_fat = grand_totals['fat_percentage_sum'] / grand_totals['customer_count'] if grand_totals['customer_count'] > 0 else 0
                avg_snf = grand_totals['snf_percentage_sum'] / grand_totals['customer_count'] if grand_totals['customer_count'] > 0 else 0
                page_data.append([
                    'TOTAL :',
                    f"{grand_totals['customer_count']} Customers",
                    f"{grand_totals['total_weight']:.2f}",
                    f"{avg_fat:.2f}",
                    f"{grand_totals['total_fat_kg']:.3f}",
                    f"{avg_snf:.2f}",
                    f"{grand_totals['total_snf_kg']:.3f}",
                    f"{grand_totals['purchase_amount']:.2f}",
                    f"{int(grand_totals['total_amount'])}"
                ])
            
            table = Table([header] + page_data, colWidths=col_widths, repeatRows=1)
            
            table_style = [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),  # Left align party names and phone
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]
            
            if page_num == total_pages - 1:
                table_style.extend([
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
                ])
            
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f'Page {page_num + 1} of {total_pages}',
                styles['PageNumber']
            ))
            
            if page_num < total_pages - 1:
                elements.append(PageBreak())
        
        elements.append(PageBreak())
        return elements

    def _generate_customer_milk_bill(self, collections, doc, styles):
        """Generate the customer milk bill section"""
        elements = []
        
        dairy_info = DairyInformation.objects.filter(author=self.request.user, is_active=True).first()
        dairy_name = dairy_info.dairy_name if dairy_info else self.request.user.username
        elements.append(Paragraph(f'<u>{dairy_name}</u>', styles['DairyName']))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph('MILK BILL', styles['ReportTitle']))
        
        start_date = collections.aggregate(min_date=Min('collection_date'))['min_date']
        end_date = collections.aggregate(max_date=Max('collection_date'))['max_date']
        customer = collections.first().customer
        
        elements.append(Paragraph(f"Customer: {customer.id}-{customer.name}", styles['CustomerName']))
        if customer.phone:
            elements.append(Paragraph(f"Phone: {customer.phone}", styles['CustomerPhone']))
        
        elements.append(Paragraph(
            f"Period: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        data = []
        header = ['DATE', 'TIME', 'TYPE', 'KG', 'FAT %', 'FAT KG', 'SNF %', 'SNF KG', 'RATE', 'AMOUNT']
        data.append(header)
        
        # Initialize totals
        totals = {
            'total_kg': 0,
            'total_fat_kg': 0,
            'total_snf_kg': 0,
            'total_amount': 0,
            'fat_percentage_sum': 0,
            'snf_percentage_sum': 0,
            'count': 0
        }
        
        for collection in collections.order_by('collection_date', 'collection_time'):
            row = [
                collection.collection_date.strftime('%d/%m/%Y'),
                collection.get_collection_time_display(),
                collection.get_milk_type_display(),
                f"{collection.kg:.2f}",
                f"{collection.fat_percentage:.2f}",
                f"{collection.fat_kg:.3f}",
                f"{collection.snf_percentage:.2f}",
                f"{collection.snf_kg:.3f}",
                f"{collection.rate:.2f}",
                f"{collection.amount:.2f}"
            ]
            data.append(row)
            
            # Update totals
            totals['total_kg'] += collection.kg
            totals['total_fat_kg'] += collection.fat_kg
            totals['total_snf_kg'] += collection.snf_kg
            totals['total_amount'] += collection.amount
            totals['fat_percentage_sum'] += collection.fat_percentage
            totals['snf_percentage_sum'] += collection.snf_percentage
            totals['count'] += 1
        
        # Add totals row
        avg_fat = totals['fat_percentage_sum'] / totals['count'] if totals['count'] > 0 else 0
        avg_snf = totals['snf_percentage_sum'] / totals['count'] if totals['count'] > 0 else 0
        totals_row = [
            'TOTAL', '', '',
            f"{totals['total_kg']:.2f}",
            f"{avg_fat:.2f}",
            f"{totals['total_fat_kg']:.3f}",
            f"{avg_snf:.2f}",
            f"{totals['total_snf_kg']:.3f}",
            '',
            f"{totals['total_amount']:.2f}"
        ]
        data.append(totals_row)

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (-2, 1), (-2, -1), 'RIGHT'),
        ]))
        
        elements.append(table)
        elements.append(PageBreak())
        return elements

    @action(detail=False, methods=['get'])
    def generate_report(self, request):
        """Generate a milk purchase report PDF for the given date range"""
        # Get date range from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not all([start_date, end_date]):
            return Response(
                {'error': 'start_date and end_date are required query parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get collections for the date range
        collections = Collection.objects.filter(
            author=request.user,
            collection_date__gte=start_date,
            collection_date__lte=end_date
        ).select_related('customer')
        
        if not collections.exists():
            return Response(
                {'error': 'No collections found for the specified date range'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Get styles and define common styles once
        styles = getSampleStyleSheet()
        
        # Add custom styles that will be used across reports
        styles.add(ParagraphStyle(
            name='DairyName',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=5,
            alignment=1  # Center alignment
        ))

        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=10,
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='DateRange',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=0  # Left alignment
        ))

        styles.add(ParagraphStyle(
            name='UserName',
            parent=styles['Normal'],
            fontSize=13,
            fontName='Helvetica-Bold',
            spaceAfter=5,
            alignment=0
        ))

        styles.add(ParagraphStyle(
            name='PageNumber',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=5,
            alignment=0  # Left alignment
        ))

        styles.add(ParagraphStyle(
            name='PartyName',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=2,
            alignment=0  # Left alignment
        ))

        # Add the missing CustomerName and CustomerPhone styles
        styles.add(ParagraphStyle(
            name='CustomerName',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=2,
            alignment=0  # Left alignment
        ))

        styles.add(ParagraphStyle(
            name='CustomerPhone',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=2,
            alignment=0  # Left alignment
        ))
        
        # Generate all elements
        elements = []
        
        # Add title and date range
        title = Paragraph(f"Milk Collection Report ({start_date} to {end_date})", styles['CustomTitle'])
        elements.append(title)
        
        # Add purchase report
        elements.extend(self._generate_purchase_report(collections, doc, styles))
        
        # Add milk purchase summary (removed extra spacing since we now force page break)
        elements.extend(self._generate_milk_purchase_summary(collections, doc, styles))
        
        # Add individual customer milk bills (start on new page)
        customers = Customer.objects.filter(collection__in=collections).distinct()
        for customer in customers:
            customer_collections = collections.filter(customer=customer)
            if customer_collections.exists():
                elements.extend(self._generate_customer_milk_bill(
                    customer_collections, doc, styles
                ))
                if customer != customers.last():
                    elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="milk_report_{start_date}_to_{end_date}.pdf"'
        
        return response

    @action(detail=False, methods=['get'])
    def generate_customer_report(self, request):
        """Generate milk bill PDF for specific customers"""
        # Get date range and customer IDs from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        customer_ids = request.query_params.get('customer_ids')
        
        if not all([start_date, end_date, customer_ids]):
            return Response(
                {'error': 'start_date, end_date, and customer_ids are required query parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            customer_ids = [int(id.strip()) for id in customer_ids.split(',')]
        except ValueError:
            return Response(
                {'error': 'Invalid date format (use YYYY-MM-DD) or customer IDs format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # First, check if all customers belong to the user
        user_customer_ids = set(Customer.objects.filter(
            author=request.user,
            id__in=customer_ids
        ).values_list('id', flat=True))
        
        invalid_customer_ids = set(customer_ids) - user_customer_ids
        if invalid_customer_ids:
            return Response(
                {
                    'error': 'Cannot generate report for customers that do not belong to you',
                    'invalid_customer_ids': list(invalid_customer_ids)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get collections for the date range and specified customers
        collections = Collection.objects.filter(
            author=request.user,
            collection_date__gte=start_date,
            collection_date__lte=end_date,
            customer_id__in=customer_ids
        ).select_related('customer')
        
        if not collections.exists():
            return Response(
                {'error': 'No collections found for the specified customers and date range'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Get styles and define common styles
        styles = getSampleStyleSheet()
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='DairyName',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=5,
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=10,
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='DateRange',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=0  # Left alignment
        ))
        
        styles.add(ParagraphStyle(
            name='CustomerName',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=2,
            alignment=0  # Left alignment
        ))

        styles.add(ParagraphStyle(
            name='CustomerPhone',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=2,
            alignment=0  # Left alignment
        ))
        
        styles.add(ParagraphStyle(
            name='PageNumber',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1  # Center alignment
        ))
        
        # Generate elements
        elements = []
        
        # Get customers in the specified list
        customers = Customer.objects.filter(
            id__in=customer_ids,
            author=request.user
        )
        
        # Generate milk bill for each customer
        for customer in customers:
            customer_collections = collections.filter(customer=customer)
            if customer_collections.exists():
                elements.extend(self._generate_customer_milk_bill(
                    customer_collections, doc, styles
                ))
                if customer != customers.last():
                    elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="customer_reports_{start_date}_to_{end_date}.pdf"'
        
        return response

