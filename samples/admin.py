from django.contrib import admin
from django.utils.html import format_html
from .models import Sample, StorageLocation, QuantityLog

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'temperature', 'created_at')
    list_filter = ('location_type',)
    search_fields = ('name', 'location_type')

class QuantityLogInline(admin.TabularInline):
    model = QuantityLog
    extra = 0
    readonly_fields = ('change_type', 'quantity_change', 'quantity_after', 'reason', 'changed_by', 'changed_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'name', 'sample_type', 'created_by', 'storage_location', 
                    'quantity', 'unit', 'alert_status_display', 'barcode_preview', 'created_at')
    list_filter = ('sample_type', 'storage_location', 'created_at', 'expiration_date')
    search_fields = ('sample_id', 'name', 'sample_type')
    inlines = [QuantityLogInline]
    
    def get_readonly_fields(self, request, obj=None):
        """Only show alert_status_display when editing existing objects"""
        if obj:  # Editing an existing object
            return ('id', 'sample_id', 'created_at', 'updated_at', 'barcode_preview', 'alert_status_display')
        else:  # Creating a new object
            return ('id', 'sample_id', 'created_at', 'updated_at', 'barcode_preview')
    
    def get_fieldsets(self, request, obj=None):
        """Only show alert status for existing objects"""
        if obj:  # Editing an existing object
            return (
                ('Basic Information', {
                    'fields': ('sample_id', 'name', 'sample_type', 'created_by')
                }),
                ('Quantity & Storage', {
                    'fields': ('quantity', 'unit', 'min_quantity', 'storage_location')
                }),
                ('Expiration', {
                    'fields': ('expiration_date',)
                }),
                ('System Information', {
                    'fields': ('id', 'created_at', 'updated_at', 'barcode_preview', 'alert_status_display'),
                    'classes': ('collapse',)
                }),
            )
        else:  # Creating a new object
            return (
                ('Basic Information', {
                    'fields': ('name', 'sample_type', 'created_by')
                }),
                ('Quantity & Storage', {
                    'fields': ('quantity', 'unit', 'min_quantity', 'storage_location')
                }),
                ('Expiration', {
                    'fields': ('expiration_date',)
                }),
            )
    
    def barcode_preview(self, obj):
        if obj and obj.sample_id:
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
    
    def alert_status_display(self, obj):
        """Display alert status with color coding"""
        if not obj:
            return "Save to see alerts"
            
        alerts = obj.get_alert_status()
        
        if not alerts:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ No Alerts</span>'
            )
        
        alert_html = []
        for alert in alerts:
            if alert['severity'] == 'critical':
                color = 'red'
                icon = '🔴'
            else:
                color = 'orange'
                icon = '⚠️'
            
            alert_html.append(
                f'<div style="color: {color}; margin: 2px 0;">{icon} {alert["message"]}</div>'
            )
        
        return format_html(''.join(alert_html))
    
    alert_status_display.short_description = "Alert Status"

@admin.register(QuantityLog)
class QuantityLogAdmin(admin.ModelAdmin):
    list_display = ('sample', 'change_type', 'quantity_change', 'quantity_after', 'changed_by', 'changed_at')
    list_filter = ('change_type', 'changed_at', 'changed_by')
    search_fields = ('sample__sample_id', 'sample__name', 'reason')
    readonly_fields = ('sample', 'change_type', 'quantity_change', 'quantity_after', 'reason', 'changed_by', 'changed_at')
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False