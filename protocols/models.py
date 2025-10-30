from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import uuid

class ProtocolCategory(models.Model):
    """Categories for organizing protocols (e.g., DNA Extraction, Cell Culture, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#667eea', help_text="Hex color code for UI display")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Protocol Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Protocol(models.Model):
    """Standard Operating Procedures and Protocol Templates"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    title = models.CharField(max_length=200)
    protocol_code = models.CharField(max_length=50, blank=True, 
                                      help_text="Unique protocol identifier (e.g., SOP-001)")
    category = models.ForeignKey(ProtocolCategory, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='protocols')
    description = models.TextField(blank=True, help_text="Brief overview of the protocol")
    
    # Rich Text Content
    objective = RichTextField(blank=True, help_text="Purpose and goals of this protocol")
    materials = RichTextField(blank=True, help_text="Required materials, equipment, and reagents")
    procedure = RichTextField(blank=True, help_text="Step-by-step instructions")
    safety_notes = RichTextField(blank=True, help_text="Safety precautions and warnings")
    troubleshooting = RichTextField(blank=True, help_text="Common issues and solutions")
    references = RichTextField(blank=True, help_text="Citations and related protocols")
    notes = RichTextField(blank=True, help_text="Additional notes and comments")
    
    # Versioning
    version = models.IntegerField(default=1, help_text="Protocol version number")
    is_active = models.BooleanField(default=True, help_text="Active version for use")
    parent_protocol = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, 
                                        blank=True, related_name='versions',
                                        help_text="Original protocol if this is a version")
    
    # Approval Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                     blank=True, related_name='protocols_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, 
                                    related_name='protocols_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usage tracking
    times_used = models.IntegerField(default=0, help_text="Number of experiments using this protocol")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.protocol_code} v{self.version} - {self.title}"
    
    @classmethod
    def generate_protocol_code(cls):
        """Generate next available protocol code"""
        last_protocol = cls.objects.filter(
            protocol_code__startswith='SOP-'
        ).order_by('protocol_code').last()
        
        if last_protocol:
            # Extract number from last code and increment
            try:
                last_number = int(last_protocol.protocol_code.split('-')[1])
                new_number = last_number + 1
            except (IndexError, ValueError):
                new_number = 1
        else:
            new_number = 1
        
        return f'SOP-{new_number:03d}'
    
    def save(self, *args, **kwargs):
        """Auto-generate protocol code if not provided"""
        if not self.protocol_code:
            max_attempts = 100
            for attempt in range(max_attempts):
                candidate_code = self.generate_protocol_code()
                if not Protocol.objects.filter(protocol_code=candidate_code).exists():
                    self.protocol_code = candidate_code
                    break
            else:
                raise ValueError("Could not generate unique protocol code")
        
        super().save(*args, **kwargs)
    
    def create_new_version(self, updated_by):
        """Create a new version of this protocol"""
        # Find the root protocol
        root_protocol = self.parent_protocol if self.parent_protocol else self
        
        # Get the latest version number
        latest_version = Protocol.objects.filter(
            protocol_code=root_protocol.protocol_code
        ).order_by('-version').first()
        
        new_version_number = (latest_version.version if latest_version else 0) + 1
        
        # Deactivate all previous versions
        Protocol.objects.filter(protocol_code=root_protocol.protocol_code).update(is_active=False)
        
        # Create new version
        new_protocol = Protocol.objects.create(
            title=self.title,
            protocol_code=self.protocol_code,
            category=self.category,
            description=self.description,
            objective=self.objective,
            materials=self.materials,
            procedure=self.procedure,
            safety_notes=self.safety_notes,
            troubleshooting=self.troubleshooting,
            references=self.references,
            notes=self.notes,
            version=new_version_number,
            is_active=True,
            parent_protocol=root_protocol,
            status='DRAFT',
            created_by=updated_by
        )
        
        return new_protocol
    
    def clone_for_new_protocol(self, new_title, created_by):
        """Clone this protocol as a new independent protocol"""
        new_protocol = Protocol.objects.create(
            title=new_title,
            # protocol_code will be auto-generated
            category=self.category,
            description=self.description,
            objective=self.objective,
            materials=self.materials,
            procedure=self.procedure,
            safety_notes=self.safety_notes,
            troubleshooting=self.troubleshooting,
            references=self.references,
            notes=f"Cloned from {self.protocol_code} v{self.version}\n\n{self.notes}",
            version=1,
            is_active=True,
            status='DRAFT',
            created_by=created_by
        )
        
        return new_protocol
    
    def approve(self, approved_by):
        """Approve this protocol"""
        from django.utils import timezone
        
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()
    
    def archive(self):
        """Archive this protocol"""
        self.status = 'ARCHIVED'
        self.is_active = False
        self.save()
    
    def increment_usage(self):
        """Increment usage counter when protocol is used in experiment"""
        self.times_used += 1
        self.save()
    
    def get_all_versions(self):
        """Get all versions of this protocol"""
        root = self.parent_protocol if self.parent_protocol else self
        return Protocol.objects.filter(
            models.Q(id=root.id) | models.Q(parent_protocol=root)
        ).order_by('version')
    
    def get_active_version(self):
        """Get the currently active version"""
        root = self.parent_protocol if self.parent_protocol else self
        return Protocol.objects.filter(
            protocol_code=root.protocol_code,
            is_active=True
        ).first()