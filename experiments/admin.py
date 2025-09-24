from django.contrib import admin
from .models import Experiment

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'description')
    filter_horizontal = ('samples',)
    readonly_fields = ('id', 'created_at', 'updated_at')