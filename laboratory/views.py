from rest_framework import viewsets
from .models import LabResult
from .serializers import LabResultSerializer


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer