from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .services import save_with_version

User = get_user_model()

def _create_version_on_save(instance):
    """
    یک خطی: هنگام ذخیره یک شیء مدل، ورژن جدیدی در سیستم ثبت می‌کند.
    
    توضیح مفصل: این تابع کمکی یک ورژن (history) برای نمونهٔ مدل داده‌شده ایجاد می‌کند. ابتدا تلاش می‌کند عامل (user) انجام‌دهندهٔ تغییر را از فیلدهای مرسوم نمونه استخراج کند: به ترتیب created_by، سپس updated_by و سپس primary_doctor — در هر مورد فقط در صورتی استفاده می‌شود که مقدار مربوط یک نمونه از مدل کاربر (User) باشد. اگر از این مسیرها کاربری پیدا نشد و تنظیمات شامل SYSTEM_USER_ID باشد، تلاش می‌کند کاربر سیستم را با آن شناسه بارگذاری کند؛ در صورت عدم وجود آن کاربر این خطا را نادیده می‌گیرد و ادامه می‌دهد. در نهایت تابع داخلی save_with_version با آرگومان‌های (instance, user, reason='auto-signal') فراخوانی می‌شود؛ بدین صورت یا یک ورژن مرتبط با کاربر پیدا‌شده ایجاد می‌شود یا (اگر کاربر None باشد) ورژنی بدون عامل مشخص ثبت می‌گردد.
    
    اثرات جانبی: ایجاد یا ثبت یک ورژن از طریق save_with_version. هیچ استثنایی در مسیر افتادن کاربر سیستمی به بیرون پرتاب نمی‌شود (خطای عدم وجود کاربر صامت نادیده گرفته می‌شود).
    """
    # Try to get the user from various sources
    user = None
    
    # Check if instance has created_by or updated_by that are User instances
    if hasattr(instance, 'created_by') and isinstance(instance.created_by, User):
        user = instance.created_by
    elif hasattr(instance, 'updated_by') and isinstance(instance.updated_by, User):
        user = instance.updated_by
    elif hasattr(instance, 'primary_doctor') and isinstance(instance.primary_doctor, User):
        user = instance.primary_doctor
    
    # If no user found, use system user if configured
    if user is None and hasattr(settings, 'SYSTEM_USER_ID'):
        try:
            user = User.objects.get(id=settings.SYSTEM_USER_ID)
        except User.DoesNotExist:
            pass
    
    save_with_version(instance, user, reason='auto-signal')

# Patient signal
@receiver(post_save, sender='patients_core.Patient')
def patient_saved(sender, instance, created, **kwargs):
    """
    ثبت‌کنندهٔ سیگنال post_save برای مدل patients_core.Patient.
    
    این گیرنده پس از ذخیرهٔ یک نمونهٔ Patient فراخوانی می‌شود و مسئول ایجاد یک ورژن تاریخچه برای آن است؛ خودِ کار ایجاد ورژن از طریق تابع کمکی _create_version_on_save انجام می‌شود که کاربر عامل را از فیلدهای مرتبط (مثل created_by، updated_by یا primary_doctor) تعیین کرده و در صورت نیاز از SYSTEM_USER_ID استفاده می‌کند. این تابع هیچ مقداری برنمی‌گرداند و در صورت نیافتن کاربر سیستمی خطا را بی‌صدا نادیده می‌گیرد.
    
    Parameters:
        instance: نمونهٔ ذخیره‌شدهٔ مدل Patient؛ این نمونه به _create_version_on_save منتقل می‌شود.
        created (bool): نشان می‌دهد آیا نمونه تازه ایجاد شده است یا نه. (در این گیرنده استفادهٔ مستقیم ندارد)
    """
    _create_version_on_save(instance)

# Encounter signal
@receiver(post_save, sender='diab_encounters.Encounter')
def encounter_saved(sender, instance, created, **kwargs):
    """
    ایونت گیر برای post_save مدل Encounter که پس از ذخیره، یک نسخهٔ تاریخچه (version) از نمونه ایجاد می‌کند.
    
    این تابع به عنوان گیرندهٔ سیگنال `post_save` برای `diab_encounters.Encounter` ثبت می‌شود و صرفاً فراخوانی کمکی `_create_version_on_save(instance)` را انجام می‌دهد. این کمکی کاربر مرتبط را از فیلدهای نمونه (مانند `created_by`, `updated_by`, یا `primary_doctor`) یا با استفاده از `settings.SYSTEM_USER_ID` تعیین می‌کند و سپس با دلیل `'auto-signal'` نسخه را ذخیره می‌کند. تابع خود خطاهای نبودن کاربر سیستمی را صامت مدیریت می‌کند و خروجی‌ای برنمی‌گرداند.
    
    Parameters:
        sender: کلاس یا شناسهٔ ارسال‌کنندهٔ سیگنال (معمولاً رشتهٔ `diab_encounters.Encounter`).
        instance: نمونهٔ مدل که ذخیره شده و قرار است برای آن نسخه‌برداری انجام شود.
        created (bool): نشان‌دهندهٔ این که آیا نمونه تازه ایجاد شده است یا به‌روزرسانی شده.
        **kwargs: سایر آرگومان‌های اضافی سیگنال (بی‌تاثیر بر عملکرد این گیرنده).
    """
    _create_version_on_save(instance)

# LabResult signal
@receiver(post_save, sender='diab_labs.LabResult')
def lab_result_saved(sender, instance, created, **kwargs):
    """
    ایونت‌ریسیور post_save برای مدل LabResult که پس از ذخیره شدن نمونه، یک ورژن جدید ایجاد می‌کند.
    
    این تابع به عنوان گیرنده سیگنال post_save برای `diab_labs.LabResult` ثبت شده است و فقط وظیفه‌ی ایجاد یک ورژن جدید از نمونهٔ ذخیره‌شده را دارد. ایجاد ورژن از طریق فراخوانی تابع کمکی `_create_version_on_save(instance)` انجام می‌شود که کاربر عمل‌کننده را از فیلدهای مرتبط (مثل `created_by`, `updated_by`, `primary_doctor`) یا از کاربر سیستمی تعریف‌شده در تنظیمات تعیین می‌کند و سپس `save_with_version` را با دلیل `'auto-signal'` فراخوانی می‌نماید.
    
    Parameters:
        instance: نمونهٔ مدل LabResult که تازه ذخیره شده و برای آن باید ورژن ساخته شود.
    """
    _create_version_on_save(instance)

# MedicationOrder signal
@receiver(post_save, sender='diab_medications.MedicationOrder')
def medication_order_saved(sender, instance, created, **kwargs):
    """
    ایونت post_save برای MedicationOrder را هندل می‌کند و برای هر ذخیره‌شدن، نسخه‌ای (version) ایجاد می‌کند.
    
    این گیرنده سیگنال برای sender برابر با 'diab_medications.MedicationOrder' ثبت می‌شود و هنگام فراخوانی، تابع داخلی `_create_version_on_save` را با نمونهٔ ذخیره‌شده اجرا می‌کند تا یک ورژن با reason='auto-signal' ساخته شود. تابع مقدار بازگشتی ندارد و خطاهای احتمالی مربوط به یافتن کاربر سیستم را ساکت می‌کند.
    
    Parameters:
        instance: نمونهٔ MedicationOrder که پس از ذخیره ارسال شده — این نمونه برای ایجاد ورژن استفاده می‌شود.
        created (bool): نشان می‌دهد آیا نمونه تازه ساخته شده (True) یا به‌روزرسانی شده (False)؛ این تابع رفتار متفاوتی بر اساس این مقدار انجام نمی‌دهد اما از امضای استاندارد سیگنال پیروی می‌کند.
    """
    _create_version_on_save(instance)