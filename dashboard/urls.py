from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard-home'),
    path('samples/', views.dashboard_samples, name='dashboard-samples'),
    path('experiments/', views.dashboard_experiments, name='dashboard-experiments'),
    path('experiments/<uuid:experiment_id>/', views.dashboard_experiment_detail, name='dashboard-experiment-detail'),
    path('experiments/<uuid:experiment_id>/upload/', views.dashboard_experiment_upload, name='dashboard-experiment-upload'),
    path('storage/', views.dashboard_storage, name='dashboard-storage'),
    path('alerts/', views.dashboard_alerts, name='dashboard-alerts'),
    path('lineage/', views.dashboard_lineage, name='dashboard-lineage'),
]