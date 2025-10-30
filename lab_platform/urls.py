from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('samples.urls')),
    path('api/', include('experiments.urls')),
    path('api/', include('protocols.urls')),
    path('api/dashboard/stats/', dashboard_views.dashboard_stats),
    path('api/dashboard/storage/', dashboard_views.storage_utilization),
    path('api/dashboard/activity/', dashboard_views.recent_activity),
    path('api/dashboard/analytics/', dashboard_views.sample_analytics),
    path('dashboard/', include('dashboard.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)