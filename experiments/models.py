from django.db import models
from django.contrib.auth.models import User
from samples.models import Sample
from ckeditor.fields import RichTextField
import uuid
from protocols.models import Protocol

class Experiment(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Link to protocol template
    protocol_template = models.ForeignKey(
        Protocol, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='experiments_using',
        help_text="Protocol template used for this experiment"
    )
    
    # Rich text fields for detailed documentation
    objective = RichTextField(blank=True, help_text="Experiment objectives and goals")
    materials = RichTextField(blank=True, help_text="Materials and reagents used")
    procedure = RichTextField(blank=True, help_text="Detailed experimental procedure")
    results = RichTextField(blank=True, help_text="Results and observations")
    conclusion = RichTextField(blank=True, help_text="Conclusions and next steps")
    notes = RichTextField(blank=True, help_text="Additional notes and comments")
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments_created')
    samples = models.ManyToManyField(Sample, blank=True, related_name='experiments')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title