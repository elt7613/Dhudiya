from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollectionViewSet, CustomerViewSet,
    MarketMilkPriceViewSet, DairyInformationViewSet
)

router = DefaultRouter()
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'market-milk-prices', MarketMilkPriceViewSet, basename='market-milk-price')
router.register(r'dairy-information', DairyInformationViewSet, basename='dairy-information')

urlpatterns = [
    path('', include(router.urls)),
] 