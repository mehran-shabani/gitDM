from rest_framework import viewsets
from .models import ClinicalReference
from .serializers import ClinicalReferenceSerializer


class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer