from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.dashboard_stats, name='dashboard-stats'),
    path('storage/', views.storage_utilization, name='storage-utilization'),
    path('activity/', views.recent_activity, name='recent-activity'),
    path('analytics/', views.sample_analytics, name='sample-analytics'),
]