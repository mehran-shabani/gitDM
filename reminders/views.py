from datetime import datetime
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from gitdm.permissions import IsDoctor
from gitdm.models import PatientProfile
from .models import Reminder
from .serializers import ReminderSerializer
from .services import ensure_upcoming_reminders, send_due_notifications


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = (IsAuthenticated, IsDoctor)

    def get_queryset(self):
        user = self.request.user
        # Limit to reminders for patients under current doctor
        return Reminder.objects.filter(patient__primary_doctor=user).select_related('patient')
    @action(detail=False, methods=['post'], url_path='generate')
    def generate_for_patient(self, request):
        """
        Generate upcoming reminders for a given patient_id.
        Body: {"patient_id": "<uuid>"}
        """
        pid = request.data.get('patient_id')
        if not pid:
            return Response({'detail': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = PatientProfile.objects.get(id=pid, primary_doctor=request.user)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient not found or not accessible'}, status=status.HTTP_404_NOT_FOUND)
        created = ensure_upcoming_reminders(patient, created_by=request.user)
        return Response({'created': len(created)})

# File: reminders/views.py

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
# … other imports …

class ReminderViewSet(...):

    @action(detail=False, methods=['get'], url_path='due')
    def list_due(self, request):
        """
        List due reminders for current doctor patients.
        Optional query: ?patient_id=<uuid>
        """
        qs = self.get_queryset().filter(status=Reminder.Status.PENDING)

        pid = request.query_params.get('patient_id')
        if pid:
            qs = qs.filter(patient_id=pid)

        now = timezone.now()
        # only include reminders whose due_at is past AND either never snoozed or snooze_until passed
        qs = (
            qs.filter(due_at__lte=now)
              .filter(Q(snooze_until__isnull=True) | Q(snooze_until__lte=now))
              .order_by('due_at')
        )

        count = qs.count()
        data = self.get_serializer(qs, many=True).data
        return Response({'count': count, 'results': data})
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.complete()
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'])
    def snooze(self, request, pk=None):
        reminder = self.get_object()
        until = request.data.get('until')
        if not until:
            return Response({'detail': 'until is required (ISO datetime)'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            dt = datetime.fromisoformat(until)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
        except Exception:
            return Response({'detail': 'Invalid datetime format'}, status=status.HTTP_400_BAD_REQUEST)
        reminder.snooze(dt)
        return Response({'status': 'snoozed', 'until': reminder.snooze_until})

    @action(detail=False, methods=['post'], url_path='notify-due')
    def notify_due(self, request):
        """
        Send Notification entries for all due reminders for a given patient.
        Body: {"patient_id": "<uuid>"}
        """
        pid = request.data.get('patient_id')
        if not pid:
            return Response({'detail': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = PatientProfile.objects.get(id=pid, primary_doctor=request.user)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient not found or not accessible'}, status=status.HTTP_404_NOT_FOUND)
        count = send_due_notifications(patient, recipient=request.user)
        return Response({'notifications_created': count})

