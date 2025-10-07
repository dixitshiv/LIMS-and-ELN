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
    
    def record_quantity_change(self, change_type, quantity_change, changed_by, reason=''):
        """
        Record a quantity change and update the sample quantity
        
        Args:
            change_type: One of the CHANGE_TYPES choices from QuantityLog
            quantity_change: The amount to add (positive) or subtract (negative)
            changed_by: User object who made the change
            reason: Optional reason for the change
        """
        from decimal import Decimal
        
        # Calculate new quantity
        new_quantity = self.quantity + Decimal(str(quantity_change))
        
        # Validate that quantity doesn't go negative
        if new_quantity < 0:
            raise ValueError(f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {quantity_change}")
        
        # Update sample quantity
        self.quantity = new_quantity
        self.save()
        
        # Create log entry
        QuantityLog.objects.create(
            sample=self,
            change_type=change_type,
            quantity_change=quantity_change,
            quantity_after=new_quantity,
            reason=reason,
            changed_by=changed_by
        )
        
        return self.quantity
    
    def use_quantity(self, amount, changed_by, reason=''):
        """Helper method to record sample usage (decreases quantity)"""
        from decimal import Decimal
        return self.record_quantity_change('USE', -Decimal(str(amount)), changed_by, reason)
    
    def add_quantity(self, amount, changed_by, reason=''):
        """Helper method to add quantity to sample"""
        from decimal import Decimal
        return self.record_quantity_change('ADD', Decimal(str(amount)), changed_by, reason)
    
    def adjust_quantity(self, amount, changed_by, reason=''):
        """Helper method for manual quantity adjustments"""
        from decimal import Decimal
        return self.record_quantity_change('ADJUST', Decimal(str(amount)), changed_by, reason)

    def __str__(self):
        return f"{self.sample_id} - {self.name}"

class QuantityLog(models.Model):
    CHANGE_TYPES = [
        ('USE', 'Used in experiment'),
        ('ADD', 'Quantity added'),
        ('ADJUST', 'Manual adjustment'),
        ('SPLIT', 'Split into aliquots'),
        ('DISPOSE', 'Disposed'),
    ]
    
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='quantity_logs')
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPES)
    quantity_change = models.DecimalField(max_digits=10, decimal_places=3)  # Positive or negative
    quantity_after = models.DecimalField(max_digits=10, decimal_places=3)  # Quantity after change
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.sample.sample_id} - {self.change_type} - {self.quantity_change} {self.sample.unit}"