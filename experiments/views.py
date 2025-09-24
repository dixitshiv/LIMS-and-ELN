from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Experiment
from .serializers import ExperimentSerializer

class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)