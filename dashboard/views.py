from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from samples.models import Sample, StorageLocation
from experiments.models import Experiment
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Return overall dashboard statistics
    """
    # Basic counts
    total_samples = Sample.objects.count()
    total_storage_locations = StorageLocation.objects.count()
    total_experiments = Experiment.objects.count()
    
    # Samples by type
    samples_by_type = Sample.objects.values('sample_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Samples by storage location
    samples_by_location = Sample.objects.values(
        'storage_location__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_samples = Sample.objects.filter(created_at__gte=week_ago).count()
    recent_experiments = Experiment.objects.filter(created_at__gte=week_ago).count()
    
    return Response({
        'overview': {
            'total_samples': total_samples,
            'total_storage_locations': total_storage_locations,
            'total_experiments': total_experiments,
        },
        'samples_by_type': list(samples_by_type),
        'samples_by_location': list(samples_by_location),
        'recent_activity': {
            'samples_last_7_days': recent_samples,
            'experiments_last_7_days': recent_experiments,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def storage_utilization(request):
    """
    Return storage location utilization data
    """
    storage_stats = StorageLocation.objects.annotate(
        sample_count=Count('sample')
    ).values(
        'id', 'name', 'location_type', 'sample_count'
    ).order_by('-sample_count')
    
    return Response({
        'storage_locations': list(storage_stats)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity(request):
    """
    Return recent samples and experiments
    """
    # Get last 10 samples
    recent_samples = Sample.objects.select_related('created_by', 'storage_location').order_by('-created_at')[:10]
    
    # Get last 10 experiments
    recent_experiments = Experiment.objects.select_related('created_by').order_by('-created_at')[:10]
    
    samples_data = []
    for sample in recent_samples:
        samples_data.append({
            'id': str(sample.id),
            'sample_id': sample.sample_id,
            'name': sample.name,
            'sample_type': sample.sample_type,
            'created_by': sample.created_by.username,
            'created_at': sample.created_at,
            'storage_location': sample.storage_location.name if sample.storage_location else None
        })
    
    experiments_data = []
    for experiment in recent_experiments:
        experiments_data.append({
            'id': str(experiment.id),
            'title': experiment.title,
            'created_by': experiment.created_by.username,
            'created_at': experiment.created_at,
            'sample_count': experiment.samples.count()
        })
    
    return Response({
        'recent_samples': samples_data,
        'recent_experiments': experiments_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sample_analytics(request):
    """
    Return detailed sample analytics
    """
    # Samples created per day for last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    daily_samples = Sample.objects.filter(
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Top sample types
    top_sample_types = Sample.objects.values('sample_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Top creators
    top_creators = Sample.objects.values('created_by__username').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return Response({
        'daily_creation_trend': list(daily_samples),
        'top_sample_types': list(top_sample_types),
        'top_creators': list(top_creators)
    })
@login_required
def dashboard_home(request):
    """Render the main dashboard page"""
    return render(request, 'dashboard/home.html')

@login_required
def dashboard_samples(request):
    """Render the samples overview page"""
    return render(request, 'dashboard/samples.html')

@login_required
def dashboard_storage(request):
    """Render the storage utilization page"""
    return render(request, 'dashboard/storage.html')

@login_required
def dashboard_alerts(request):
    """Render the alerts page"""
    return render(request, 'dashboard/alerts.html')

@login_required
def dashboard_lineage(request):
    """Render the sample lineage page"""
    return render(request, 'dashboard/lineage.html')