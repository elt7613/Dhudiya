from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('user.urls')),
    path('api/collector/', include('collector.urls')),
    path('api/', include('wallet.urls')),
]
