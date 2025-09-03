from __future__ import annotations
import logging
from datetime import timedelta
from typing import Final
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from gitdm.models import PatientProfile
from notifications.models import Notification
from notifications.services import NotificationService
from .models import Reminder


logger = logging.getLogger(__name__)
User = get_user_model()


DEFAULT_CADENCE_DAYS: Final[dict[str, int]] = {
    Reminder.ReminderType.HBA1C: 90,
    Reminder.ReminderType.FBS: 30,
    Reminder.ReminderType.TWO_HPP: 30,
    Reminder.ReminderType.BUN: 180,
    Reminder.ReminderType.CR: 180,
    Reminder.ReminderType.ALT: 180,
    Reminder.ReminderType.AST: 180,
    Reminder.ReminderType.ALP: 180,
    Reminder.ReminderType.URINE_24H_PROTEIN: 365,
    Reminder.ReminderType.EYE_EXAM: 365,
    Reminder.ReminderType.EMG: 365,
    Reminder.ReminderType.NCV: 365,
    Reminder.ReminderType.TSH: 365,
    Reminder.ReminderType.BMI: 30,
    Reminder.ReminderType.DIET: 30,
}


def get_next_due_date(last_anchor: timezone.datetime, reminder_type: str) -> timezone.datetime:
    days = DEFAULT_CADENCE_DAYS.get(reminder_type, 90)
    return last_anchor + timedelta(days=days)


def ensure_upcoming_reminders(patient: PatientProfile, created_by: User | None = None) -> list[Reminder]:
    """
    Ensure at least one upcoming reminder exists for each known type.
    If none exists (pending/scheduled in future or pending past due), create one anchored to now.
    """
    created: list[Reminder] = []
    now = timezone.now()
    for rtype in DEFAULT_CADENCE_DAYS.keys():
        q = Reminder.objects.filter(patient=patient, reminder_type=rtype).order_by('-due_at')
        latest = q.first()
        if latest and latest.status in (Reminder.Status.PENDING, Reminder.Status.SENT) and latest.due_at >= now:
            continue
        if latest and latest.status == Reminder.Status.COMPLETED and latest.completed_at:
            anchor = latest.completed_at
        elif latest:
            anchor = latest.due_at
        else:
            anchor = patient.created_at
        due_at = get_next_due_date(anchor, rtype)
        title = f"Reminder: {rtype}"
        reminder = Reminder.objects.create(
            patient=patient,
            created_by=created_by,
            reminder_type=rtype,
            title=title,
            description=f"Scheduled reminder for {rtype}",
            due_at=due_at,
            status=Reminder.Status.PENDING,
        )
        created.append(reminder)
    return created


def send_due_notifications(patient: PatientProfile, recipient: User) -> int:
    """
    Create Notification entries for all due reminders of a patient.
    Returns the count of notifications created.
    """
    now = timezone.now()
    qs = (
        Reminder.objects.select_for_update(skip_locked=True)
        .filter(
            patient=patient,
            status=Reminder.Status.PENDING,
            due_at__lte=now,
        )
        .filter(Q(snooze_until__isnull=True) | Q(snooze_until__lte=now))
        .order_by('due_at')
    )

    sent_ids: list[int] = []
    with transaction.atomic():
        for r in qs:
            NotificationService.create_notification(
                recipient=recipient,
                title=r.title,
                message=r.description or f"Reminder is due: {r.reminder_type}",
                notification_type=Notification.NotificationType.REMINDER,
                priority='HIGH' if r.priority in ('HIGH', 'URGENT') else 'MEDIUM',
                patient_id=str(patient.id),
                resource_type='reminder',
                resource_id=str(r.id),
                expires_at=None,
            )
            sent_ids.append(r.id)

        if sent_ids:
            Reminder.objects.filter(id__in=sent_ids).update(status=Reminder.Status.SENT)

    return len(sent_ids)

