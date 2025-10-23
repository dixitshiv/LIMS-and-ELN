from django.db import models
from django.contrib.auth.models import User
from .models import Experiment
import os
import uuid

def experiment_file_path(instance, filename):
    """Generate file path for experiment attachments"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Generate new filename
    filename = f'{uuid.uuid4()}.{ext}'
    # Return path: media/experiments/experiment_id/filename
    return os.path.join('experiments', str(instance.experiment.id), filename)

class FileAttachment(models.Model):
    FILE_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('PDF', 'PDF Document'),
        ('EXCEL', 'Excel Spreadsheet'),
        ('WORD', 'Word Document'),
        ('DATA', 'Data File'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=experiment_file_path)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.IntegerField(help_text="File size in bytes")
    description = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.experiment.title}"
    
    def get_file_extension(self):
        """Get file extension"""
        return os.path.splitext(self.file_name)[1].lower()
    
    def determine_file_type(self):
        """Automatically determine file type from extension"""
        ext = self.get_file_extension()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']
        if ext in image_extensions:
            return 'IMAGE'
        elif ext == '.pdf':
            return 'PDF'
        elif ext in ['.xls', '.xlsx', '.csv']:
            return 'EXCEL'
        elif ext in ['.doc', '.docx']:
            return 'WORD'
        elif ext in ['.txt', '.json', '.xml', '.csv']:
            return 'DATA'
        else:
            return 'OTHER'
    
    def save(self, *args, **kwargs):
        """Auto-set file type and size on save"""
        if not self.file_type:
            self.file_type = self.determine_file_type()
        
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)