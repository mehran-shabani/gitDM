from rest_framework import viewsets
from .models import MedicationOrder
from .serializers import MedicationOrderSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer