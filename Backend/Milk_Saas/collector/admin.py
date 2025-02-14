from django.contrib import admin
from .models import Customer, Collection, RateStep, MarketMilkPrice


@admin.register(MarketMilkPrice)
class MarketMilkPriceAdmin(admin.ModelAdmin):
    list_display = ('price', 'author', 'is_active', 'created_at')
    list_filter = ('is_active', 'author')
    search_fields = ('price',)

    def get_queryset(self, request):
        return MarketMilkPrice.all_objects.all()

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'author', 'is_active')
    list_filter = ('is_active', 'author')
    search_fields = ('name', 'phone')
    list_per_page = 20

    def get_queryset(self, request):
        return Customer.all_objects.all()

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'collection_date', 'collection_time', 
                   'milk_type', 'measured', 'liters', 'kg', 
                   'fat_percentage','fat_kg', 'snf_percentage','snf_kg', 'rate', 
                   'amount', 'author', 'is_active')
    list_filter = ('is_active', 'collection_time', 'milk_type', 
                  'measured', 'collection_date', 'author')
    search_fields = ('customer__name',)
    date_hierarchy = 'collection_date'
    list_per_page = 20

    def get_queryset(self, request):
        return Collection.all_objects.all().select_related(
            'customer', 'author'
        )

@admin.register(RateStep)
class RateStepAdmin(admin.ModelAdmin):
    list_display = ('milk_type', 'rate_type', 'author', 'is_active', 'created_at')
    list_filter = ('milk_type', 'rate_type', 'is_active', 'author')
    search_fields = ('milk_type', 'rate_type')

    def get_queryset(self, request):
        return RateStep.all_objects.all()
