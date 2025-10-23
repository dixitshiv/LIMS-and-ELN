from django.contrib import admin
from .models import Experiment
from .file_models import FileAttachment

class FileAttachmentInline(admin.TabularInline):
    model = FileAttachment
    extra = 0
    readonly_fields = ('id', 'file_name', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at')
    fields = ('file', 'description')
    
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, FileAttachment):
                if not instance.uploaded_by_id:
                    instance.uploaded_by = request.user
                    instance.file_name = instance.file.name
                instance.save()
        formset.save_m2m()

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'start_date', 'end_date', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'created_by', 'start_date')
    search_fields = ('title', 'description', 'objective', 'procedure')
    filter_horizontal = ('samples',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [FileAttachmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'status', 'created_by')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Documentation', {
            'fields': ('objective', 'materials', 'procedure', 'results', 'conclusion', 'notes'),
            'classes': ('wide',)
        }),
        ('Samples', {
            'fields': ('samples',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, FileAttachment):
                if not instance.uploaded_by_id:
                    instance.uploaded_by = request.user
                    instance.file_name = instance.file.name
                instance.save()
        formset.save_m2m()

@admin.register(FileAttachment)
class FileAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'experiment', 'file_type', 'file_size_display', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('file_name', 'description', 'experiment__title')
    readonly_fields = ('id', 'file_type', 'file_size', 'uploaded_at')
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    file_size_display.short_description = 'File Size'
    
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)