import threading
from django.db import transaction
from django.forms.models import model_to_dict
from django.apps import apps
from .models import RecordVersion

_thread_state = threading.local()

IGNORE_FIELDS = {"id", "pk", "created_at", "updated_at"}

RESOURCE_MAP = {
    'Patient': ('patients_core', 'Patient'),
    'Encounter': ('diab_encounters', 'Encounter'),
    'LabResult': ('diab_labs', 'LabResult'),
    'MedicationOrder': ('diab_medications', 'MedicationOrder'),
}

def _compute_snapshot(instance):
    """
    یک اسنَپ‌شات (نمایه) از یک نمونه مدل Django می‌سازد و آمادهٔ ذخیره/مقایسه می‌کند.
    
    شرح:
        این تابع از model_to_dict برای تبدیل یک نمونه مدل به دیکشنری استفاده می‌کند و سپس مقادیر شبیه به UUID
        (آبجکت‌هایی که صفت `hex` دارند) را به رشته تبدیل می‌کند تا برای سریال‌سازی JSON مناسب شوند.
        تابع هیچ فیلدی را حذف یا فیلتر نمی‌کند و تنها نوع برخی مقادیر را برای سازگاری تبدیل می‌کند.
    
    Parameters:
        instance (django.db.models.Model): نمونهٔ مدل Django یا هر آبجکتی که توسط `model_to_dict` قابل تبدیل باشد.
    
    Returns:
        dict: دیکشنریِ فیلدها و مقادیرِ نمونه که UUID-مانندها به رشته تبدیل شده‌اند.
    """
    d = model_to_dict(instance)
    # Convert UUIDs to strings for JSON serialization
    for key, value in d.items():
        if hasattr(value, 'hex'):  # UUID objects have hex attribute
            d[key] = str(value)
    return d

def _compute_diff(prev, curr):
    """
    یک دیکشنری اختلاف (diff) بین دو snapshot قبلی و جاری تولید می‌کند.
    
    جزئیات:
    - اگر snapshot قبلی (prev) تهی یا فالس باشد، None برمی‌گرداند (هیچ مقایسه‌ای انجام نمی‌شود).
    - برای همه کلیدهای موجود در هر دو snapshot، مقادیر را مقایسه می‌کند و در صورت تغییر، برای آن کلید یک ورودی به شکل {"from": مقدار_قبلی, "to": مقدار_جاری} اضافه می‌کند.
    - کلیدهایی که در مجموعه IGNORE_FIELDS قرار دارند نادیده گرفته می‌شوند و در diff لحاظ نمی‌شوند.
    - اگر هیچ اختلافی یافت نشود، None برمی‌گرداند؛ در غیر این صورت یک دیکشنری از اختلاف‌ها را برمی‌گرداند.
    
    پارامترها:
    - prev: دیکشنری snapshot قبلی (یا مقدار فالس در صورت عدم وجود).
    - curr: دیکشنری snapshot جاری.
    
    مقدار بازگشتی:
    - دیکشنری اختلاف‌ها یا None در صورت عدم وجود prev یا عدم وجود تغییرات.
    """
    if not prev:
        return None
    keys = set(prev.keys()) | set(curr.keys())
    delta = {}
    for k in keys:
        if k in IGNORE_FIELDS:
            continue
        pv, cv = prev.get(k), curr.get(k)
        if pv != cv:
            delta[k] = {"from": pv, "to": cv}
    return delta or None

@transaction.atomic
def save_with_version(instance, user, reason=""):
    """
    ذخیرهٔ نسخه‌ای (version) از یک نمونهٔ مدل در جدول RecordVersion.
    
    این تابع برای نمونهٔ داده‌شده یک اسنَپ‌شات (snapshot) از فیلدهای مدل ایجاد می‌کند، آن را با آخرین نسخهٔ ثبت‌شده مقایسه (diff) می‌نماید و یک رکورد جدید در RecordVersion می‌سازد که شامل شمارهٔ نسخهٔ بعدی، شمارهٔ نسخهٔ قبلی، اسنَپ‌شات فعلی، دیفِف (در صورت وجود)، متا شامل دلیل و کاربری که تغییر را انجام داده است می‌باشد. برای جلوگیری از فراخوانی‌های تو در تو (re-entrant) که می‌تواند به ایجاد نسخه‌های تکراری منجر شود، از یک فلَگ thread-local (_thread_state.in_version) استفاده می‌کند: اگر فلَگ از قبل ست شده باشد تابع بلافاصله بازمی‌گردد و نسخه‌ای ساخته نمی‌شود. در هر صورت در پایان اجرای تابع فلَگ بازنشانی می‌شود.
    
    - اگر نسخهٔ پیشین وجود نداشته باشد، شمارهٔ نسخهٔ بعدی 1 تعیین می‌شود و prev_version برابر None خواهد بود.
    - مقدار diff می‌تواند None باشد (مثلاً وقتی نسخهٔ قبلی وجود ندارد یا هیچ اختلافی بین اسنَپ‌شات‌ها یافت نشود).
    - اثر جانبی اصلی: ایجاد یک رکورد جدید در مدل RecordVersion.
    
    Parameters:
        instance: نمونهٔ مدل Django که باید از آن اسنَپ‌شات گرفته و نسخه‌گذاری شود — تنها فیلدهای قابل سریالایز در اسنَپ‌شات لحاظ می‌شوند.
        user: کاربری که تغییر را ایجاد کرده و به‌عنوان changed_by در رکورد نسخه ذخیره می‌شود.
        reason (str): متن مختصری که در metaِ نسخه ذخیره می‌شود تا دلیل ایجاد نسخه را ثبت کند.
    
    Return:
        None
    """
    if getattr(_thread_state, 'in_version', False):
        return
    _thread_state.in_version = True
    try:
        rtype = instance.__class__.__name__
        rid = getattr(instance, 'id')
        curr = _compute_snapshot(instance)
        last = (RecordVersion.objects
                .filter(resource_type=rtype, resource_id=rid)
                .order_by('-version')
                .first())
        next_ver = 1 if not last else last.version + 1
        prev_snap = None if not last else last.snapshot
        diff = _compute_diff(prev_snap, curr)
        RecordVersion.objects.create(
            resource_type=rtype,
            resource_id=rid,
            version=next_ver,
            prev_version=None if not last else last.version,
            snapshot=curr,
            diff=diff,
            meta={"reason": reason},
            changed_by=user,
        )
    finally:
        _thread_state.in_version = False

@transaction.atomic
def revert_to_version(resource_type: str, resource_id, target_version: int, user, reason="revert"):
    """
    شیء منبع مشخص را به یک نسخهٔ تاریخی بازمی‌گرداند و بازگردانی را به‌عنوان یک نسخهٔ جدید ثبت می‌کند.
    
    جزئیات:
    - ورودی‌ها:
      - resource_type: نوع منبع (کلید موجود در RESOURCE_MAP) که برای یافتن مدل واقعی استفاده می‌شود.
      - resource_id: شناسهٔ رکورد زنده‌ای که قرار است بازگردانی شود.
      - target_version: شمارهٔ نسخهٔ هدف که snapshot آن اعمال خواهد شد.
      - user: کاربری که عملیات بازگردانی را انجام می‌دهد و به‌عنوان تغییردهندهٔ نسخهٔ جدید ثبت می‌شود.
      - reason: متن توضیحی اختیاری که در متادیتای نسخهٔ ثبت‌شده قرار می‌گیرد (پیش‌فرض "revert").
    
    - عملکرد:
      1. مدل مربوط به resource_type را از RESOURCE_MAP بارگذاری می‌کند و نمونهٔ جاری با id برابر resource_id را از دیتابیس بازیابی می‌کند.
      2. نسخهٔ هدف (RecordVersion) را بر اساس resource_type، resource_id و target_version بار می‌گیرد.
      3. مقادیر ذخیره‌شده در snapshot نسخهٔ هدف را روی نمونهٔ جاری اعمال می‌کند؛ فیلدهای موجود در IGNORE_FIELDS (مثلاً "id", "pk", "created_at", "updated_at") نادیده گرفته می‌شوند.
      4. شیء را تنها با فیلدهایی که در snapshot وجود دارند (به جز IGNORE_FIELDS) ذخیره می‌کند تا فقط آن فیلدها در پایگاه داده به‌روزرسانی شوند.
      5. پس از اعمال snapshot، یک نسخهٔ جدید از وضعیت فعلی با فراخوانی save_with_version ثبت می‌شود تا بازگردانی نیز در تاریخچهٔ نسخه‌ها قابل ردیابی باشد.
      6. نمونهٔ به‌روز‌شده را بازمی‌گرداند.
    
    تأثیرات جانبی مهم:
    - رکورد هدف در دیتابیس تغییر می‌کند (به‌روزرسانیِ فیلدهای snapshot).
    - یک RecordVersion جدید ثبت می‌شود که نشان‌دهندهٔ بازگردانی است.
    
    تذکرهای عملی:
    - تابع مستقیماً از ORM برای بارگذاری مدل و نسخه‌ها استفاده می‌کند؛ در صورت وجود نداشتن مدل یا نسخهٔ درخواستی، استثناهای استاندارد ORM (مثل DoesNotExist) از سمت فراخوانده‌کننده مدیریت می‌شوند.
    """
    Model = apps.get_model(*RESOURCE_MAP[resource_type])
    obj = Model.objects.get(id=resource_id)
    target = RecordVersion.objects.get(resource_type=resource_type, resource_id=resource_id, version=target_version)
    # اعمال snapshot بر روی شیء
    for k, v in target.snapshot.items():
        if k in IGNORE_FIELDS:
            continue
        setattr(obj, k, v)
    obj.save(update_fields=[k for k in target.snapshot.keys() if k not in IGNORE_FIELDS])
    # ثبت نسخهٔ جدید پس از بازگردانی
    save_with_version(obj, user, reason=f"{reason}: to v{target_version}")
    return obj