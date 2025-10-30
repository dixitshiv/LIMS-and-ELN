from django.contrib import admin
from django.utils.html import format_html
from .models import Protocol, ProtocolCategory

@admin.register(ProtocolCategory)
class ProtocolCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'protocol_count', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def color_display(self, obj):
        """Display color swatch"""
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = "Color"
    
    def protocol_count(self, obj):
        """Display count of protocols in this category"""
        count = obj.protocols.count()
        return format_html(
            '<span style="background: #e3f2fd; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{}</span>',
            count
        )
    protocol_count.short_description = "Protocols"


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    list_display = ('protocol_code', 'title', 'version', 'status', 'category', 
                    'is_active', 'times_used', 'created_by', 'approved_by', 'created_at')
    list_filter = ('status', 'is_active', 'category', 'created_at', 'approved_at')
    search_fields = ('title', 'protocol_code', 'description', 'procedure')
    readonly_fields = ('id', 'protocol_code', 'created_at', 'updated_at', 
                       'times_used', 'approved_at', 'version_history_display')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('protocol_code', 'title', 'category', 'description', 'created_by')
        }),
        ('Content', {
            'fields': ('objective', 'materials', 'procedure', 'safety_notes', 
                      'troubleshooting', 'references', 'notes'),
            'classes': ('wide',)
        }),
        ('Versioning', {
            'fields': ('version', 'is_active', 'parent_protocol', 'version_history_display')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('System Information', {
            'fields': ('id', 'times_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def version_history_display(self, obj):
        """Display all versions of this protocol"""
        if not obj.id:
            return "Save to see version history"
        
        versions = obj.get_all_versions()
        
        if versions.count() == 1:
            return format_html('<span style="color: #999;">No other versions</span>')
        
        version_html = []
        for protocol in versions:
            url = f'/admin/protocols/protocol/{protocol.id}/change/'
            active = "✓ " if protocol.is_active else ""
            status_color = {
                'DRAFT': '#ff9800',
                'REVIEW': '#2196f3',
                'APPROVED': '#4caf50',
                'ARCHIVED': '#9e9e9e'
            }.get(protocol.status, '#999')
            
            version_html.append(
                f'<li><a href="{url}" style="color: #447e9b; text-decoration: none;">'
                f'{active}v{protocol.version}</a> - '
                f'<span style="color: {status_color}; font-weight: bold;">{protocol.status}</span> '
                f'<span style="color: #666; font-size: 0.9em;">({protocol.created_at.strftime("%Y-%m-%d")})</span></li>'
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          ''.join(version_html))
    
    version_history_display.short_description = "Version History"
    
    actions = ['approve_protocols', 'archive_protocols', 'create_new_version']
    
    def approve_protocols(self, request, queryset):
        """Approve selected protocols"""
        count = 0
        for protocol in queryset:
            if protocol.status != 'APPROVED':
                protocol.approve(request.user)
                count += 1
        
        self.message_user(request, f'{count} protocol(s) approved successfully.')
    approve_protocols.short_description = "Approve selected protocols"
    
    def archive_protocols(self, request, queryset):
        """Archive selected protocols"""
        count = queryset.update(status='ARCHIVED', is_active=False)
        self.message_user(request, f'{count} protocol(s) archived successfully.')
    archive_protocols.short_description = "Archive selected protocols"
    
    def create_new_version(self, request, queryset):
        """Create new versions of selected protocols"""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one protocol to create a new version.', level='error')
            return
        
        protocol = queryset.first()
        new_protocol = protocol.create_new_version(request.user)
        
        self.message_user(request, 
            f'New version created: {new_protocol.protocol_code} v{new_protocol.version}')
    create_new_version.short_description = "Create new version"