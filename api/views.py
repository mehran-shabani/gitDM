from rest_framework import viewsets, filters
from rest_framework.response import Response
from clinical_refs.models import ClinicalReference
from .serializers import ClinicalReferenceSerializer

class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','topic','section','source']

    def get_queryset(self):
        qs = super().get_queryset()
        topic = self.request.query_params.get('topic')
        year = self.request.query_params.get('year')
        source = self.request.query_params.get('source')
        q = self.request.query_params.get('q')
        if topic:
            qs = qs.filter(topic__icontains=topic)
        if year:
            qs = qs.filter(year=year)
        if source:
            qs = qs.filter(source__icontains=source)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs