from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CollectionViewSet, CustomerViewSet, RateChartViewSet, MarketMilkPriceViewSet

router = DefaultRouter()
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'rate-charts', RateChartViewSet, basename='rate-chart')
router.register(r'market-milk-prices', MarketMilkPriceViewSet, basename='market-milk-price')

urlpatterns = [
    path('', include(router.urls)),
] 