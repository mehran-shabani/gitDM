from django.core.management.base import BaseCommand
from django.utils import timezone
from timeline.services import ReminderService


class Command(BaseCommand):
    help = 'ارسال یادآورهای آزمایشات سررسید'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش یادآورهای قابل ارسال بدون ارسال واقعی',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('حالت آزمایشی - یادآورها ارسال نمی‌شوند')
            
            # نمایش یادآورهای قابل ارسال
            overdue = ReminderService.get_overdue_reminders()
            upcoming = ReminderService.get_upcoming_reminders()
            
            self.stdout.write(f'یادآورهای عقب‌افتاده: {overdue.count()}')
            for reminder in overdue:
                self.stdout.write(f'  - {reminder.patient.full_name}: {reminder.get_test_type_display()}')
            
            self.stdout.write(f'یادآورهای آتی: {upcoming.count()}')
            for reminder in upcoming:
                self.stdout.write(f'  - {reminder.patient.full_name}: {reminder.get_test_type_display()}')
        
        else:
            notifications_sent = ReminderService.send_reminder_notifications()
            self.stdout.write(
                self.style.SUCCESS(
                    f'{notifications_sent} یادآوری ارسال شد در {timezone.now()}'
                )
            )