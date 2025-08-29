from django.apps import AppConfig

class RecordsVersioningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'records_versioning'

    def ready(self):
        """
        واردکنندهٔ تنبلِ ماژول سیگنال‌ها برای ثبت هندلرهای سیگنال هنگام راه‌اندازی اپلیکیشن.
        
        این متد هنگام راه‌اندازی اپلیکیشن (phaseٔ ready در چرخهٔ عمر Django AppConfig) ماژول `signals` را به‌صورت محلی وارد می‌کند تا هر کدی که در آن ماژول مسئول ثبت هندلرهای سیگنال است اجرا شود. این کار از ثبت سیگنال‌ها در زمان ایمپورت ماژول‌های سطح بالا جلوگیری کرده و تضمین می‌کند که هندلرها در زمان مناسب (پس از آماده‌شدن کانفیگ اپ) ثبت شوند. متد مقدار برگشتی ندارد و خطایی را به‌صورت مستقیم پرتاب نمی‌کند؛ هر خطای ناشی از واردسازی ماژول `signals` مانند بقیه‌ی خطاهای ایمپورت رفتار می‌شود.
        """
        from . import signals  # noqa