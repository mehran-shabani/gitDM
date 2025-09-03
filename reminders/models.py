from django.db import models
from django.conf import settings
from django.utils import timezone


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
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('URGENT', 'Urgent'),
        ],
        default='MEDIUM'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_at', 'id']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['reminder_type']),
        ]

    def __str__(self) -> str:
        return f"{self.reminder_type} for {self.patient} due {self.due_at}"

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

