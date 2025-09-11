from django.core.management.base import BaseCommand
from timeline.models import ReminderTemplate, TestReminder


class Command(BaseCommand):
    help = 'ایجاد قالب‌های پیش‌فرض یادآوری آزمایشات'
    
    def handle(self, *args, **options):
        templates_data = [
            {
                'test_type': 'HBA1C',
                'default_frequency': 'QUARTERLY',
                'default_priority': 'HIGH',
                'default_reminder_days': 14,
                'instructions': 'آزمایش HbA1c برای کنترل میانگین قند خون در ۳ ماه گذشته',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'FBS',
                'default_frequency': 'MONTHLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 7,
                'instructions': 'آزمایش قند ناشتا برای کنترل روزانه قند خون',
                'preparation_notes': '۸-۱۲ ساعت ناشتا بودن الزامی است'
            },
            {
                'test_type': '2HPP',
                'default_frequency': 'MONTHLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 7,
                'instructions': 'آزمایش قند ۲ ساعت بعد از غذا',
                'preparation_notes': 'دقیقاً ۲ ساعت بعد از شروع غذا خوردن'
            },
            {
                'test_type': 'BUN',
                'default_frequency': 'QUARTERLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 10,
                'instructions': 'آزمایش اوره خون برای بررسی عملکرد کلیه',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'CR',
                'default_frequency': 'QUARTERLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 10,
                'instructions': 'آزمایش کراتینین برای بررسی عملکرد کلیه',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'ALT',
                'default_frequency': 'BIANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 14,
                'instructions': 'آزمایش آنزیم کبدی ALT',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'AST',
                'default_frequency': 'BIANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 14,
                'instructions': 'آزمایش آنزیم کبدی AST',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'ALP',
                'default_frequency': 'BIANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 14,
                'instructions': 'آزمایش آنزیم آلکالین فسفاتاز',
                'preparation_notes': 'نیازی به ناشتا بودن ندارد'
            },
            {
                'test_type': 'PR_URINE_24',
                'default_frequency': 'QUARTERLY',
                'default_priority': 'HIGH',
                'default_reminder_days': 14,
                'instructions': 'آزمایش پروتئین ادرار ۲۴ ساعته برای بررسی عملکرد کلیه',
                'preparation_notes': 'جمع‌آوری ادرار در مدت ۲۴ ساعت کامل'
            },
            {
                'test_type': 'EYE_EXAM',
                'default_frequency': 'ANNUALLY',
                'default_priority': 'HIGH',
                'default_reminder_days': 30,
                'instructions': 'معاینه چشم توسط متخصص چشم برای تشخیص عوارض دیابتی',
                'preparation_notes': 'احتمالاً نیاز به گشاد کردن مردمک چشم'
            },
            {
                'test_type': 'EMG',
                'default_frequency': 'ANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 30,
                'instructions': 'الکترومایوگرافی برای بررسی عملکرد عضلات',
                'preparation_notes': 'پوست باید تمیز و خشک باشد'
            },
            {
                'test_type': 'NCV',
                'default_frequency': 'ANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 30,
                'instructions': 'آزمایش سرعت رسانش عصبی برای تشخیص نوروپاتی',
                'preparation_notes': 'دست‌ها و پاها باید گرم باشند'
            },
            {
                'test_type': 'TSH',
                'default_frequency': 'ANNUALLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 21,
                'instructions': 'آزمایش هورمون محرک تیروئید',
                'preparation_notes': 'ترجیحاً در صبح و ناشتا'
            },
            {
                'test_type': 'BMI',
                'default_frequency': 'MONTHLY',
                'default_priority': 'LOW',
                'default_reminder_days': 3,
                'instructions': 'اندازه‌گیری شاخص توده بدنی (وزن و قد)',
                'preparation_notes': 'اندازه‌گیری در صبح و با لباس سبک'
            },
            {
                'test_type': 'BP',
                'default_frequency': 'WEEKLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 2,
                'instructions': 'اندازه‌گیری فشار خون',
                'preparation_notes': 'آرامش ۵ دقیقه‌ای قبل از اندازه‌گیری'
            },
            {
                'test_type': 'DIET',
                'default_frequency': 'QUARTERLY',
                'default_priority': 'MEDIUM',
                'default_reminder_days': 14,
                'instructions': 'مشاوره تغذیه و بررسی رژیم غذایی',
                'preparation_notes': 'آماده کردن فهرست غذاهای مصرفی در هفته گذشته'
            },
            {
                'test_type': 'EXERCISE',
                'default_frequency': 'MONTHLY',
                'default_priority': 'LOW',
                'default_reminder_days': 7,
                'instructions': 'بررسی و تنظیم برنامه ورزشی',
                'preparation_notes': 'ثبت فعالیت‌های ورزشی انجام شده'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates_data:
            template, created = ReminderTemplate.objects.update_or_create(
                test_type=template_data['test_type'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'قالب جدید ایجاد شد: {template.get_test_type_display()}')
            else:
                updated_count += 1
                self.stdout.write(f'قالب به‌روزرسانی شد: {template.get_test_type_display()}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'تکمیل شد: {created_count} قالب جدید، {updated_count} قالب به‌روزرسانی'
            )
        )