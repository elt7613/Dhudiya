from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch, Sum, Avg, F, Min, Max
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime, timedelta
from .models import Collection, Customer, RateStep, MarketMilkPrice
from .serializers import (
    CollectionListSerializer, 
    CollectionDetailSerializer,
    CustomerSerializer,
    RateStepSerializer,
    MarketMilkPriceSerializer
)
from .filters import CollectionFilter, RateStepFilter

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

    def _generate_purchase_report(self, collections, doc, styles):
        """Generate the purchase report section with pagination support"""
        elements = []
        
        # Add user's name at top left
        user_name = collections.first().author.username if collections.exists() else self.request.user.username
        elements.append(Paragraph(user_name, styles['UserName']))
        elements.append(Spacer(1, 5))
        
        # Add title (centered and underlined)
        elements.append(Paragraph('<u>PURCHASE REPORT</u>', styles['ReportTitle']))
        
        # Get date range
        start_date = collections.aggregate(min_date=Min('collection_date'))['min_date']
        end_date = collections.aggregate(max_date=Max('collection_date'))['max_date']
        
        # Add date range
        elements.append(Paragraph(
            f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        # Group by date and calculate totals
        daily_data = []
        header = ['DATE', 'WEIGHT (KG)', 'LITERS', 'FAT %', 'FAT KG.', 'SNF %', 'SNF KG.', 'AMOUNT RS.']
        
        # Initialize grand totals
        grand_totals = {
            'total_kg': 0,
            'total_liters': 0,
            'total_fat_kg': 0,
            'total_snf_kg': 0,
            'total_amount': 0,
            'fat_percentage_sum': 0,
            'snf_percentage_sum': 0,
            'count': 0
        }
        
        # Collect all daily data
        for date in collections.values('collection_date').distinct().order_by('collection_date'):
            date_collections = collections.filter(collection_date=date['collection_date'])
            daily_totals = date_collections.aggregate(
                total_kg=Sum('kg'),
                total_liters=Sum('liters'),
                total_fat_kg=Sum('fat_kg'),
                total_snf_kg=Sum('snf_kg'),
                total_amount=Sum('amount'),
                avg_fat_percentage=Avg('fat_percentage'),
                avg_snf_percentage=Avg('snf_percentage')
            )
            
            # Update grand totals
            grand_totals['total_kg'] += daily_totals['total_kg']
            grand_totals['total_liters'] += daily_totals['total_liters']
            grand_totals['total_fat_kg'] += daily_totals['total_fat_kg']
            grand_totals['total_snf_kg'] += daily_totals['total_snf_kg']
            grand_totals['total_amount'] += daily_totals['total_amount']
            grand_totals['fat_percentage_sum'] += daily_totals['avg_fat_percentage']
            grand_totals['snf_percentage_sum'] += daily_totals['avg_snf_percentage']
            grand_totals['count'] += 1
            
            daily_data.append([
                date['collection_date'].strftime('%d/%m/%Y'),
                f"{daily_totals['total_kg']:.2f}",
                f"{daily_totals['total_liters']:.2f}",
                f"{daily_totals['avg_fat_percentage']:.2f}",
                f"{daily_totals['total_fat_kg']:.3f}",
                f"{daily_totals['avg_snf_percentage']:.2f}",
                f"{daily_totals['total_snf_kg']:.3f}",
                f"{daily_totals['total_amount']:.2f}"
            ])

        # Calculate how many rows can fit on one page (excluding header and totals)
        # This is an estimate based on the page size and row heights
        rows_per_page = 25  # Adjust this number based on testing with your actual data
        
        # Split data into pages
        total_rows = len(daily_data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        # Create table with specific column widths
        col_widths = [
            doc.width * 0.15,  # DATE
            doc.width * 0.12, # WEIGHT
            doc.width * 0.12, # LITERS
            doc.width * 0.12, # FAT %
            doc.width * 0.12, # FAT KG
            doc.width * 0.12, # SNF %
            doc.width * 0.12, # SNF KG
            doc.width * 0.13  # AMOUNT
        ]

        # Process each page
        for page_num in range(total_pages):
            start_idx = page_num * rows_per_page
            end_idx = min((page_num + 1) * rows_per_page, total_rows)
            
            # Get data for current page
            page_data = daily_data[start_idx:end_idx]
            
            # Add total row only on the last page
            if page_num == total_pages - 1:
                avg_fat = grand_totals['fat_percentage_sum'] / grand_totals['count'] if grand_totals['count'] > 0 else 0
                avg_snf = grand_totals['snf_percentage_sum'] / grand_totals['count'] if grand_totals['count'] > 0 else 0
                page_data.append([
                    'TOTAL:',
                    f"{grand_totals['total_kg']:.2f}",
                    f"{grand_totals['total_liters']:.2f}",
                    f"{avg_fat:.2f}",
                    f"{grand_totals['total_fat_kg']:.3f}",
                    f"{avg_snf:.2f}",
                    f"{grand_totals['total_snf_kg']:.3f}",
                    f"{grand_totals['total_amount']:.2f}"
                ])
            
            # Create table for current page
            table = Table([header] + page_data, colWidths=col_widths)
            
            # Apply table styles
            table_style = [
                # Header style
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align dates
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                # Reduce cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]
            
            # Add total row style if this is the last page
            if page_num == total_pages - 1:
                table_style.extend([
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
                ])
            
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            
            # Add page number
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f'Page {page_num + 1} of {total_pages}',
                styles['PageNumber']
            ))
            
            # Add page break if not the last page
            if page_num < total_pages - 1:
                elements.append(PageBreak())
                # Repeat the header information on new pages
                elements.append(Paragraph(user_name, styles['UserName']))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph('<u>PURCHASE REPORT</u>', styles['ReportTitle']))
                elements.append(Paragraph(
                    f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
                    styles['DateRange']
                ))
                elements.append(Spacer(1, 8))
        
        # Add final page break after purchase report
        elements.append(PageBreak())
        return elements

    def _generate_milk_purchase_summary(self, collections, doc, styles):
        """Generate the milk purchase summary section with pagination support"""
        elements = []
        
        # Force start on new page
        elements.append(PageBreak())
        
        # Add title (centered)
        elements.append(Paragraph('MILK PURCHASE SUMMARY', styles['ReportTitle']))
        
        # Get date range
        start_date = collections.aggregate(min_date=Min('collection_date'))['min_date']
        end_date = collections.aggregate(max_date=Max('collection_date'))['max_date']
        
        # Add date range
        elements.append(Paragraph(
            f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        # Group by customer and calculate totals
        customer_data = []
        header = ['PARTY NAME', 'PHONE', 'WEIGHT', 'LITERS', 'FAT %', 'FAT Kg.', 'SNF %', 'SNF Kg.', 'TOT. AMT.']
        
        # Initialize grand totals
        grand_totals = {
            'total_weight': 0,
            'total_liters': 0,
            'total_fat_kg': 0,
            'total_snf_kg': 0,
            'total_amount': 0,
            'fat_percentage_sum': 0,
            'snf_percentage_sum': 0,
            'customer_count': 0
        }
        
        customers = Customer.objects.filter(
            collection__in=collections
        ).distinct()
        
        for customer in customers:
            customer_collections = collections.filter(customer=customer)
            customer_totals = customer_collections.aggregate(
                total_weight=Sum('kg'),
                total_liters=Sum('liters'),
                total_fat_kg=Sum('fat_kg'),
                total_snf_kg=Sum('snf_kg'),
                total_amount=Sum('amount'),
                avg_fat_percentage=Avg('fat_percentage'),
                avg_snf_percentage=Avg('snf_percentage')
            )
            
            # Update grand totals
            grand_totals['total_weight'] += customer_totals['total_weight']
            grand_totals['total_liters'] += customer_totals['total_liters']
            grand_totals['total_fat_kg'] += customer_totals['total_fat_kg']
            grand_totals['total_snf_kg'] += customer_totals['total_snf_kg']
            grand_totals['total_amount'] += customer_totals['total_amount']
            grand_totals['fat_percentage_sum'] += customer_totals['avg_fat_percentage']
            grand_totals['snf_percentage_sum'] += customer_totals['avg_snf_percentage']
            grand_totals['customer_count'] += 1
            
            customer_data.append([
                f"{customer.id}-{customer.name}",  # Combined ID and name
                customer.phone or '-',  # Phone number with fallback
                f"{customer_totals['total_weight']:.2f}",
                f"{customer_totals['total_liters']:.2f}",
                f"{customer_totals['avg_fat_percentage']:.2f}",
                f"{customer_totals['total_fat_kg']:.3f}",
                f"{customer_totals['avg_snf_percentage']:.2f}",
                f"{customer_totals['total_snf_kg']:.3f}",
                f"{customer_totals['total_amount']:.2f}"
            ])

        # Calculate how many rows can fit on one page (excluding header and totals)
        rows_per_page = 35  # Adjust this number based on testing with your actual data
        
        # Split data into pages
        total_rows = len(customer_data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        # Create table with specific column widths
        col_widths = [
            doc.width * 0.18,  # PARTY NAME
            doc.width * 0.12,  # PHONE
            doc.width * 0.10,  # WEIGHT
            doc.width * 0.10,  # LITERS
            doc.width * 0.10,  # FAT %
            doc.width * 0.10,  # FAT KG
            doc.width * 0.10,  # SNF %
            doc.width * 0.10,  # SNF KG
            doc.width * 0.10   # TOT. AMT.
        ]

        # Process each page
        for page_num in range(total_pages):
            if page_num > 0:
                # Repeat header for new pages
                elements.append(PageBreak())
                elements.append(Paragraph('MILK PURCHASE SUMMARY', styles['ReportTitle']))
                elements.append(Paragraph(
                    f"Dated from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",
                    styles['DateRange']
                ))
                elements.append(Spacer(1, 8))
            
            start_idx = page_num * rows_per_page
            end_idx = min((page_num + 1) * rows_per_page, total_rows)
            
            # Get data for current page
            page_data = customer_data[start_idx:end_idx]
            
            # Add total row only on the last page
            if page_num == total_pages - 1:
                avg_fat = grand_totals['fat_percentage_sum'] / grand_totals['customer_count'] if grand_totals['customer_count'] > 0 else 0
                avg_snf = grand_totals['snf_percentage_sum'] / grand_totals['customer_count'] if grand_totals['customer_count'] > 0 else 0
                page_data.append([
                    'TOTAL :',
                    f"{grand_totals['customer_count']} Customers",  # Show total number of customers
                    f"{grand_totals['total_weight']:.2f}",
                    f"{grand_totals['total_liters']:.2f}",
                    f"{avg_fat:.2f}",
                    f"{grand_totals['total_fat_kg']:.3f}",
                    f"{avg_snf:.2f}",
                    f"{grand_totals['total_snf_kg']:.3f}",
                    f"{grand_totals['total_amount']:.2f}"
                ])
                
                # Add final total
                page_data.append([
                    'Total Rs.',
                    '',  # Empty phone cell
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    f"{grand_totals['total_amount']:.2f}"
                ])
            
            # Create table for current page
            table = Table([header] + page_data, colWidths=col_widths)
            
            # Apply table styles
            table_style = [
                # Header style
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),  # Match purchase report font size
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),  # Right align all cells
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Left align party names
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                # Reduce cell padding
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]
            
            # Add total row style if this is the last page
            if page_num == total_pages - 1:
                table_style.extend([
                    ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
                    ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
                ])
            
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            
            # Add page number for all pages
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f'Page {page_num + 1} of {total_pages}',
                styles['PageNumber']
            ))
            
            # Add page break if not the last page
            if page_num < total_pages - 1:
                elements.append(PageBreak())
        
        # Add final page break after milk purchase summary
        elements.append(PageBreak())
        return elements

    def _generate_customer_milk_bill_v2(self, collections, customer, doc, styles):
        """Generate the milk bill section for a specific customer in the format matching the image"""
        elements = []
        
        # Force start on new page
        elements.append(PageBreak())
        
        # Add Milk Bill title
        elements.append(Paragraph("Milk Bill", styles['ReportTitle']))
        elements.append(Spacer(1, 5))
        
        # Party details
        elements.append(Paragraph(f"PARTY NAME: {customer.id}-{customer.name}", styles['PartyName']))
        elements.append(Spacer(1, 5))
        
        # Get date range
        date_range = collections.filter(customer=customer).aggregate(
            min_date=Min('collection_date'),
            max_date=Max('collection_date')
        )
        
        # Handle case where date_range values might be None
        min_date = date_range['min_date'].strftime('%d/%m/%y') if date_range['min_date'] else ''
        max_date = date_range['max_date'].strftime('%d/%m/%y') if date_range['max_date'] else ''
        
        elements.append(Paragraph(
            f"DATE FROM {min_date} TO {max_date}",
            styles['DateRange']
        ))
        elements.append(Spacer(1, 8))
        
        # Daily collection details
        daily_data = []
        header = ['DATE', 'WEIGHT', 'LITERS', 'FAT%', 'CLR', 'SNF%', 'FAT Kg.', 'FAT Rt', 'SNF Kg.', 'SNF Rt', 'RATE', 'VALUE']
        
        customer_collections = collections.filter(customer=customer).order_by('collection_date', 'collection_time')
        
        # Initialize totals
        totals = {
            'weight': 0,
            'liters': 0,
            'fat_kg': 0,
            'snf_kg': 0,
            'amount': 0,
            'fat_sum': 0,
            'snf_sum': 0,
            'count': 0
        }
        
        for collection in customer_collections:
            # Handle null values with default empty strings
            fat_rate = f"{collection.fat_rate:.2f}" if collection.fat_rate is not None else ""
            snf_rate = f"{collection.snf_rate:.2f}" if collection.snf_rate is not None else ""
            
            daily_data.append([
                collection.collection_date.strftime('%d/%m/%y'),
                f"{collection.kg:.2f}",
                f"{collection.liters:.2f}",
                f"{collection.fat_percentage:.2f}",
                f"{collection.clr:.2f}",
                f"{collection.snf_percentage:.2f}",
                f"{collection.fat_kg:.3f}",
                fat_rate,
                f"{collection.snf_kg:.3f}",
                snf_rate,
                f"{collection.rate:.2f}",
                f"{collection.amount:.2f}"
            ])
            
            # Update totals
            totals['weight'] += collection.kg
            totals['liters'] += collection.liters
            totals['fat_kg'] += collection.fat_kg
            totals['snf_kg'] += collection.snf_kg
            totals['amount'] += collection.amount
            totals['fat_sum'] += collection.fat_percentage
            totals['snf_sum'] += collection.snf_percentage
            totals['count'] += 1
        
        # Add totals row
        avg_fat = totals['fat_sum'] / totals['count'] if totals['count'] > 0 else 0
        avg_snf = totals['snf_sum'] / totals['count'] if totals['count'] > 0 else 0
        
        daily_data.append([
            'TOTAL :',
            f"{totals['weight']:.2f}",
            f"{totals['liters']:.2f}",
            f"{avg_fat:.2f}",
            '',  # CLR
            f"{avg_snf:.2f}",
            f"{totals['fat_kg']:.3f}",
            '',  # FAT Rt
            f"{totals['snf_kg']:.3f}",
            '',  # SNF Rt
            '',  # RATE
            f"{totals['amount']:.2f}"
        ])
        
        # Calculate available height for table
        available_height = doc.height - (doc.topMargin + doc.bottomMargin + 120)  # 120 for headers and spacing
        
        # Calculate row height (including padding)
        row_height = 20  # Approximate height per row in points
        
        # Calculate max rows that can fit on one page
        max_rows = int(available_height / row_height)
        
        # If data exceeds max rows, adjust font size and spacing
        if len(daily_data) + 1 > max_rows:  # +1 for header
            table_style_font_size = 8
            padding = 2
        else:
            table_style_font_size = 10
            padding = 3
        
        # Create table with specific column widths
        col_widths = [
            doc.width * 0.09,  # DATE
            doc.width * 0.08,  # WEIGHT
            doc.width * 0.08,  # LITERS
            doc.width * 0.07,  # FAT%
            doc.width * 0.07,  # CLR
            doc.width * 0.07,  # SNF%
            doc.width * 0.08,  # FAT Kg
            doc.width * 0.08,  # FAT Rt
            doc.width * 0.08,  # SNF Kg
            doc.width * 0.08,  # SNF Rt
            doc.width * 0.08,  # RATE
            doc.width * 0.14   # VALUE
        ]
        
        table = Table([header] + daily_data, colWidths=col_widths)
        
        # Apply table styles
        table_style = [
            # Header style
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), table_style_font_size),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align dates
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Reduce cell padding
            ('TOPPADDING', (0, 0), (-1, -1), padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('LEFTPADDING', (0, 0), (-1, -1), padding),
            ('RIGHTPADDING', (0, 0), (-1, -1), padding),
            # Total row style
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
        ]
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        
        return elements

    @action(detail=False, methods=['get'])
    def generate_invoice(self, request):
        """Generate a comprehensive invoice PDF containing all three report types"""
        # Get date range from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Both start_date and end_date are required query parameters'},
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
        
        # Generate all elements
        elements = []
        
        # Add title and date range
        title = Paragraph(f"Milk Collection Invoice ({start_date} to {end_date})", styles['CustomTitle'])
        elements.append(title)
        
        # Add purchase report
        elements.extend(self._generate_purchase_report(collections, doc, styles))
        
        # Add milk purchase summary (removed extra spacing since we now force page break)
        elements.extend(self._generate_milk_purchase_summary(collections, doc, styles))
        
        # Add individual customer milk bills (start on new page)
        customers = Customer.objects.filter(collection__in=collections).distinct()
        for customer in customers:
            elements.extend(self._generate_customer_milk_bill_v2(collections, customer, doc, styles))
            if customer != customers.last():
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="milk_invoice_{start_date}_to_{end_date}.pdf"'
        
        return response

class RateStepViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RateStepSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RateStepFilter
    ordering_fields = ['rate', 'fat_from', 'fat_to', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return RateStep.objects.filter(author=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()
        return Response(
            {'message': 'Rate step deleted successfully'}, 
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Rate step deleted successfully'}, status=status.HTTP_200_OK)
