from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime

class Reminder(models.Model):
    class ReminderType(models.TextChoices):
        HBA1C = 'HBA1C', 'HbA1c'
        FBS = 'FBS', 'Fasting Blood Sugar'
        TWO_HPP = '2HPP', '2-Hour Postprandial Glucose'
        BUN = 'BUN', 'Blood Urea Nitrogen'
        CR = 'CR', 'Creatinine'
        ALT = 'ALT', 'Alanine Transaminase'
        AST = 'AST', 'Aspartate Transaminase'
        ALP = 'ALP', 'Alkaline Phosphatase'
        URINE_24H_PROTEIN = 'PR_URINE_24H', '24h Urine Protein'
        EYE_EXAM = 'EYE_EXAM', 'Eye Physical Exam'
        EMG = 'EMG', 'EMG'
        NCV = 'NCV', 'NCV'
        TSH = 'TSH', 'Thyroid Stimulating Hormone'
        BMI = 'BMI', 'Body Mass Index'
        DIET = 'DIET', 'Diet/Nutrition Review'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE, related_name='reminders')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reminders'
    )
    reminder_type = models.CharField(max_length=32, choices=ReminderType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField()
    snooze_until = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('due_at', 'id')
        indexes = (
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['reminder_type']),
        )
        constraints = (
            models.CheckConstraint(
                name='completed_requires_timestamp',
                condition=(
                    models.Q(status='COMPLETED', completed_at__isnull=False) |
                    models.Q(~models.Q(status='COMPLETED'), completed_at__isnull=True)
                ),
            ),
        )

    def __str__(self) -> str:
        return f"{self.reminder_type} for {self.patient} due {self.due_at}"

    def clean(self):
        super().clean()
        # due_at و snooze_until باید aware باشن
        for field in ('due_at', 'snooze_until'):
            dt = getattr(self, field)
            if dt and timezone.is_naive(dt):
                setattr(self, field, timezone.make_aware(dt))
            # snooze در گذشته ممنوع
            if self.snooze_until and self.snooze_until <= timezone.now():
                raise ValidationError({'snooze_until': 'باید در آینده باشه'})
            # completed_at فقط وقتی status=COMPLETED
            if (self.status == self.Status.COMPLETED) ^ bool(self.completed_at):
                raise ValidationError('وضعیت و زمان تکمیل همخوان نیست')

    @property
    def is_due(self) -> bool:
        now = timezone.now()
        if self.status != self.Status.PENDING:
            return False
        if self.snooze_until and self.snooze_until > now:
            return False
        return self.due_at <= now

    def complete(self) -> None:
        if self.status not in (self.Status.COMPLETED, self.Status.CANCELLED):
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])

    def snooze(self, until: timezone.datetime) -> None:
        self.snooze_until = until
        self.save(update_fields=['snooze_until'])

