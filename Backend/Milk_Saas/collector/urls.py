from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollectionViewSet, CustomerViewSet,
    RateStepViewSet, MarketMilkPriceViewSet,
    DairyInformationViewSet
)

router = DefaultRouter()
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'rate-steps', RateStepViewSet, basename='rate-step')
router.register(r'market-milk-prices', MarketMilkPriceViewSet, basename='market-milk-price')
router.register(r'dairy-information', DairyInformationViewSet, basename='dairy-information')

urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),
] 