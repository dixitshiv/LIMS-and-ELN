from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
import base64

class StorageLocation(models.Model):
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=50)  # freezer, shelf, etc.
    temperature = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample_id = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    sample_type = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def generate_sample_id(cls):
        year = datetime.now().year
        
        # Find the last sample for this year
        last_sample = cls.objects.filter(
            sample_id__startswith=f'SAMP-{year}-'
        ).order_by('sample_id').last()
        
        if last_sample:
            # Extract number from last sample ID and increment
            last_number = int(last_sample.sample_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f'SAMP-{year}-{new_number:03d}'
    
    def save(self, *args, **kwargs):
        if not self.sample_id:
            max_attempts = 100
            for attempt in range(max_attempts):
                candidate_id = self.generate_sample_id()
                if not Sample.objects.filter(sample_id=candidate_id).exists():
                    self.sample_id = candidate_id
                    break
            else:
                raise ValueError("Could not generate unique sample ID")
        super().save(*args, **kwargs)

    def generate_barcode(self):
        """Generate barcode for sample ID"""
        code128 = Code128(self.sample_id, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def get_barcode_base64(self):
        """Get barcode as base64 string for display"""
        barcode_bytes = self.generate_barcode()
        return base64.b64encode(barcode_bytes).decode()
    
    def __str__(self):
        return f"{self.sample_id} - {self.name}"