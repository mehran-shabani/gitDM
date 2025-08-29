# ruff: noqa: RUF002
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class MedicationOrder(models.Model):

    # Frequency choices
    class FrequencyChoices(models.TextChoices):
        ONCE_DAILY = 'QD', 'Once daily'
        TWICE_DAILY = 'BID', 'Twice daily'
        THREE_TIMES_DAILY = 'TID', 'Three times daily'
        FOUR_TIMES_DAILY = 'QID', 'Four times daily'
        EVERY_6_HOURS = 'Q6H', 'Every 6 hours'
        EVERY_8_HOURS = 'Q8H', 'Every 8 hours'
        EVERY_12_HOURS = 'Q12H', 'Every 12 hours'
        AS_NEEDED = 'PRN', 'As needed'
        WEEKLY = 'QW', 'Weekly'
        MONTHLY = 'QM', 'Monthly'

    patient = models.ForeignKey(
        'core.Patient',
        on_delete=models.CASCADE,
        related_name='medication_orders',
    )
    encounter = models.ForeignKey(
        'encounters.Encounter',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='medication_orders',
    )
    atc = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]\d{2}[A-Z]{1,2}\d{2}$',
                message='ATC code must follow the format: One letter, two digits, one or two letters, two digits (e.g., A10BA02)',
            )
        ],
        help_text='ATC classification code (e.g., A10BA02 for Metformin)'
    )
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50)
    frequency = models.CharField(
        max_length=50,
        choices=FrequencyChoices.choices,
        default=FrequencyChoices.ONCE_DAILY,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date", "-id"]
        indexes = [
            models.Index(fields=["patient", "start_date"]),
            models.Index(fields=["patient", "end_date"]),
            models.Index(fields=["atc"]),
        ]

    def clean(self) -> None:
        """
        بررسی اعتبار داده‌ها و اطمینان از اینکه end_date قبل از start_date نیست.
        
        اگر فیلد end_date مقداردهی شده باشد، این متد مقادیر تاریخ‌ها را مقایسه کرده و در صورتی که end_date از start_date کوچک‌تر باشد یک ValidationError بازمی‌گرداند که خطا به‌صورت مرتبط با کلید 'end_date' برگردانده می‌شود (برای نمایش خطا در فرم‌ها یا APIهای مبتنی بر فیلد).
        """
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'End date cannot be before start date.'
            })

    def __str__(self) -> str:
        """
        یک رشتهٔ کوتاه نمایشی برای MedicationOrder را برمی‌گرداند.
        
        فرمت بازگشتی: "<نام دارو> for <نام بیمار>". مقدار <نام بیمار> از ویژگی `full_name` شیٔ مرتبط با فیلد `patient` گرفته می‌شود در صورتی که وجود داشته باشد؛ در غیر این صورت نتیجهٔ `str(self.patient)` استفاده می‌شود. این نمایش برای نمایش خلاصهٔ رکورد در رابط‌های کاربری، لاگ‌ها و انتخاب‌های متنی مناسب است.
        
        Returns:
            str: رشته‌ای با ساختمان "<name> for <patient_name>".
        """
        patient_name = getattr(self.patient, "full_name", str(self.patient))
        return f"{self.name} for {patient_name}"