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
    list_display = ('sample_id', 'name', 'sample_type', 'parent_link', 'children_count', 
                    'created_by', 'storage_location', 'quantity', 'unit', 
                    'alert_status_display', 'barcode_preview', 'created_at')
    list_filter = ('sample_type', 'storage_location', 'relationship_type', 'created_at', 'expiration_date')
    search_fields = ('sample_id', 'name', 'sample_type')
    inlines = [QuantityLogInline]
    
    # Add autocomplete for parent_sample field
    autocomplete_fields = ['parent_sample']
    
    def get_readonly_fields(self, request, obj=None):
        """Only show alert_status_display when editing existing objects"""
        if obj:  # Editing an existing object
            return ('id', 'sample_id', 'created_at', 'updated_at', 'barcode_preview', 
                    'alert_status_display', 'lineage_display', 'children_display')
        else:  # Creating a new object
            return ('id', 'sample_id', 'created_at', 'updated_at', 'barcode_preview')
    
    def get_fieldsets(self, request, obj=None):
        """Only show alert status and relationships for existing objects"""
        if obj:  # Editing an existing object
            return (
                ('Basic Information', {
                    'fields': ('sample_id', 'name', 'sample_type', 'created_by')
                }),
                ('Parent-Child Relationships', {
                    'fields': ('parent_sample', 'relationship_type', 'derivation_notes', 
                              'lineage_display', 'children_display'),
                    'classes': ('wide',)
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
                ('Parent-Child Relationships', {
                    'fields': ('parent_sample', 'relationship_type', 'derivation_notes'),
                    'classes': ('wide',)
                }),
                ('Quantity & Storage', {
                    'fields': ('quantity', 'unit', 'min_quantity', 'storage_location')
                }),
                ('Expiration', {
                    'fields': ('expiration_date',)
                }),
            )
    
    def parent_link(self, obj):
        """Display clickable link to parent sample"""
        if obj.parent_sample:
            url = f'/admin/samples/sample/{obj.parent_sample.id}/change/'
            return format_html(
                '<a href="{}" style="color: #447e9b; font-weight: bold;">📦 {}</a>',
                url,
                obj.parent_sample.sample_id
            )
        return format_html('<span style="color: #999;">—</span>')
    parent_link.short_description = "Parent Sample"
    
    def children_count(self, obj):
        """Display count of child samples with link"""
        count = obj.child_samples.count()
        if count > 0:
            return format_html(
                '<span style="background: #e3f2fd; padding: 3px 8px; border-radius: 12px; '
                'font-weight: bold; color: #1976d2;">👶 {}</span>',
                count
            )
        return format_html('<span style="color: #999;">0</span>')
    children_count.short_description = "Children"
    
    def lineage_display(self, obj):
        """Display complete ancestry chain"""
        if not obj:
            return "Save to see lineage"
        
        lineage = obj.get_lineage()
        if len(lineage) == 1:
            return format_html('<span style="color: #999;">No parent (root sample)</span>')
        
        lineage_html = []
        for i, sample in enumerate(lineage):
            if i < len(lineage) - 1:  # Not the current sample
                url = f'/admin/samples/sample/{sample.id}/change/'
                lineage_html.append(
                    f'<a href="{url}" style="color: #447e9b; text-decoration: none;">'
                    f'{sample.sample_id}</a>'
                )
            else:  # Current sample
                lineage_html.append(f'<strong>{sample.sample_id}</strong>')
        
        arrow = ' <span style="color: #999;">→</span> '
        return format_html(arrow.join(lineage_html))
    
    lineage_display.short_description = "Lineage (Root → Current)"
    
    def children_display(self, obj):
        """Display all child samples"""
        if not obj:
            return "Save to see children"
        
        children = obj.child_samples.all()
        if not children:
            return format_html('<span style="color: #999;">No child samples</span>')
        
        children_html = []
        for child in children:
            url = f'/admin/samples/sample/{child.id}/change/'
            rel_type = dict(Sample._meta.get_field('relationship_type').choices).get(
                child.relationship_type, 'Unknown'
            )
            children_html.append(
                f'<li><a href="{url}" style="color: #447e9b; text-decoration: none;">'
                f'{child.sample_id}</a> - {child.name} '
                f'<span style="color: #666; font-size: 0.9em;">({rel_type})</span></li>'
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          ''.join(children_html))
    
    children_display.short_description = "Child Samples"
    
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