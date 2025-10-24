from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Experiment
from .file_models import FileAttachment
from .serializers import ExperimentSerializer, ExperimentListSerializer
from .file_serializers import FileAttachmentSerializer

class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_by', 'start_date']
    search_fields = ['title', 'description', 'objective', 'procedure']
    ordering_fields = ['created_at', 'updated_at', 'start_date', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return ExperimentListSerializer
        return ExperimentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request, pk=None):
        """Upload a file attachment to an experiment"""
        experiment = self.get_object()
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional description
        description = request.data.get('description', '')
        
        # Create file attachment
        attachment = FileAttachment.objects.create(
            experiment=experiment,
            file=file_obj,
            file_name=file_obj.name,
            file_size=file_obj.size,
            description=description,
            uploaded_by=request.user
        )
        
        serializer = FileAttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get all file attachments for an experiment"""
        experiment = self.get_object()
        attachments = experiment.attachments.all()
        serializer = FileAttachmentSerializer(attachments, many=True, context={'request': request})
        return Response({
            'experiment_id': str(experiment.id),
            'experiment_title': experiment.title,
            'file_count': attachments.count(),
            'files': serializer.data
        })
    
    @action(detail=True, methods=['delete'], url_path='files/(?P<file_id>[^/.]+)')
    def delete_file(self, request, pk=None, file_id=None):
        """Delete a specific file attachment"""
        experiment = self.get_object()
        
        try:
            attachment = FileAttachment.objects.get(id=file_id, experiment=experiment)
            file_name = attachment.file_name
            attachment.file.delete()  # Delete actual file
            attachment.delete()  # Delete database record
            
            return Response({
                'message': f'File "{file_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        except FileAttachment.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def download_file(self, request):
        """Download a specific file by ID"""
        file_id = request.query_params.get('file_id')
        
        if not file_id:
            return Response({'error': 'file_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            attachment = FileAttachment.objects.get(id=file_id)
            
            # Open file for download
            file_handle = attachment.file.open('rb')
            response = FileResponse(file_handle, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
            
            return response
        except FileAttachment.DoesNotExist:
            raise Http404("File not found")