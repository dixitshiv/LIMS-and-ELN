from django.contrib import admin
from .models import Sample, StorageLocation

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'temperature', 'created_at')
    list_filter = ('location_type',)
    search_fields = ('name', 'location_type')

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'name', 'sample_type', 'created_by', 'storage_location', 'quantity', 'unit', 'created_at')
    list_filter = ('sample_type', 'storage_location', 'created_at')
    search_fields = ('sample_id', 'name', 'sample_type')
    readonly_fields = ('id', 'sample_id', 'created_at', 'updated_at')