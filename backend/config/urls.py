from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('patients/', include('apps.patients.urls')),
    path('', include('apps.consultations.urls')),
    path('api/sensors/', include('apps.sensors.urls')),
    path('', include('apps.ordonnances.urls')),
    path('api/', include('apps.messaging.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
