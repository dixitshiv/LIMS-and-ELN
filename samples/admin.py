from django.contrib import admin
from django.utils.html import format_html
from .models import Sample, StorageLocation

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'temperature', 'created_at')
    list_filter = ('location_type',)
    search_fields = ('name', 'location_type')

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'name', 'sample_type', 'created_by', 'storage_location', 'quantity', 'unit', 'barcode_preview', 'created_at')
    list_filter = ('sample_type', 'storage_location', 'created_at')
    search_fields = ('sample_id', 'name', 'sample_type')
    readonly_fields = ('id', 'sample_id', 'created_at', 'updated_at', 'barcode_preview')
    
    def barcode_preview(self, obj):
        if obj.sample_id:
            try:
                barcode_data = obj.get_barcode_base64()
                return format_html(
                    '<img src="data:image/png;base64,{}" height="50" style="border: 1px solid #ccc;"/>',
                    barcode_data
                )
            except Exception as e:
                return f"Barcode error: {str(e)}"
        return "No barcode available"
    barcode_preview.short_description = "Barcode Preview"