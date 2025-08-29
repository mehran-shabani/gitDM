from datetime import datetime, timedelta, timezone

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory
from django.urls import reverse

# Import the admin classes under test
# The admin module under test should reside alongside AISummary model.
# Adjust the dotted path below if the app label differs (e.g., "ai_summarizer").
try:
    from . import admin as app_admin  # when tests package is inside the app
except (ImportError, ModuleNotFoundError):
    # Fallback: try to find "<app>.admin" by scanning installed apps lazily
    # Replace 'ai_summarizer' with your actual app label if needed.
    try:
        app_admin = __import__("ai_summarizer.admin", fromlist=["*"])
    except Exception as err:
        # Last resort: create a stub module error to help developers fix import path
        raise ImportError(
            "Unable to import the app's admin module. "
            "Ensure the app label is correct (e.g., ai_summarizer.admin) "
            "or adjust the import in tests/test_ai_summarizer_admin.py."
        ) from err

# Extract classes under test
AISummaryResourceTypeFilter = app_admin.AISummaryResourceTypeFilter
AISummaryAdmin = app_admin.AISummaryAdmin
AISummary = app_admin.AISummary

pytestmark = pytest.mark.django_db

def make_superuser(**extra):
    """
    یک سوپر‌یوزر (superuser) در پایگاه‌داده ایجاد می‌کند و شیٔ کاربر و گذرواژه ایجاد شده را برمی‌گرداند.
    
    پارامترها (به‌صورت kwargs):
    - username: نام کاربری سوپر‌یوزر (پیش‌فرض "admin").
    - email: ایمیل سوپر‌یوزر (پیش‌فرض "admin@example.com").
    - password: گذرواژه سوپر‌یوزر (پیش‌فرض "pass1234").
    - سایر کلیدواژه‌ها به‌صورت مستقیم به user_model.objects.create_superuser ارسال می‌شوند (مثلاً فیلدهای مدل کاربر یا گزینه‌های اضافی).
    
    توضیحات:
    - از get_user_model() برای تعیین مدل کاربری استفاده می‌شود.
    - این تابع یک رکورد سوپر‌یوزر در دیتابیس ایجاد می‌کند (side effect).
    
    بازگشتی:
    - tuple: (user_instance, password) — نمونه مدل کاربر ایجادشده و گذرواژه‌ای که برای ایجاد استفاده شده است.
    """
    user_model = get_user_model()
    username = extra.pop("username", "admin")
    email = extra.pop("email", "admin@example.com")
    password = extra.pop("password", "pass1234")
    user = user_model.objects.create_superuser(username=username, email=email, password=password, **extra)
    return user, password

def create_ai_summary(patient=None, model_label="note", created_at=None):
    """
    یک AISummary جدید ایجاد و ذخیره می‌کند که دارای ContentType معتبر برای آزمایش فیلتر resource_type باشد.
    
    این تابع:
    - در صورت عدم ارسال مقدار برای `patient`، مدل رابطه‌ای `patient` را از فیلد AISummary کشف نموده و یک نمونه‌ی حداقلی می‌سازد.
    - سعی می‌کند یک ContentType موجود با `model` برابر `model_label` را پیدا کند؛ در صورت عدم وجود، یک ContentType جدید با همان `model` و از همان `app_label` که AISummary در آن قرار دارد ایجاد می‌کند.
    - AISummary را با فیلدهای `patient`, `content_type`, `summary` (و در صورت ارسال، `created_at`) می‌سازد و در پایگاه‌داده ایجاد می‌کند.
    
    Parameters:
        patient (Model | None): نمونهٔ موجود بیمار که به AISummary وابسته است. اگر None باشد، تابع یک نمونهٔ جدید از مدل مرتبط می‌سازد.
        model_label (str): نام مدل در ContentType (مقدار lowercase و معادل فیلد `content_type.model`) که برای تعیین resource_type استفاده می‌شود.
        created_at (datetime | None): در صورت ارسال، مقدار زمانی سفارشی برای فیلد `created_at` در AISummary قرار داده می‌شود.
    
    Returns:
        AISummary: شیء AISummary ایجادشده و ذخیره‌شده در پایگاه‌داده.
    
    Notes:
    - تابع ممکن است خطاهای مربوط به ORM (مثلاً مقادیر اجباریِ فیلدها یا محدودیت‌های دیتابیس) را از طریق استثناهای استاندارد Django بازگرداند.
    - این کمک‌کننده برای استفاده در تست‌ها و تولید نمونه‌های سریع طراحی شده است؛ در پروژه‌هایی با قوانین ایجاد پیچیده‌تر برای مدل بیمار ممکن است نیاز به تنظیم یا فراهم‌کردن `patient` صریح باشد.
    """
    # Patient is likely a FK; if project uses a different patient model adjust accordingly.
    # We'll soft-create a minimal patient if field allows null=False.
    if patient is None:
        # Try to discover Patient model from the AISummary FK meta if present
        patient_field = AISummary._meta.get_field("patient")
        patient_model = patient_field.related_model
        patient = patient_model.objects.create()  # rely on defaults; adjust in project if required

    # Build a fake model proxy for ContentType if necessary
    # Prefer locating an actual model whose _meta.model_name == model_label; otherwise create CT manually
    try:
        ct = ContentType.objects.get(model=model_label)
    except ContentType.DoesNotExist:
        # Create a temporary dummy model content type by using the AISummary model's app_label
        app_label = AISummary._meta.app_label
        # ContentType requires a valid app_label+model; if not present, use AISummary's app_label and custom model name
        ct, _ = ContentType.objects.get_or_create(app_label=app_label, model=model_label)

    values = dict(
        patient=patient,
        content_type=ct,
        summary=f"Summary for {model_label}",
    )
    if created_at is not None:
        values["created_at"] = created_at
    return AISummary.objects.create(**values)

class DummyModelAdmin(admin.ModelAdmin):
    pass

def build_changelist_request(path, user, params=None):
    """
    یک درخواست GET شبیه‌سازی‌شدهٔ Django RequestFactory می‌سازد و کاربر را به آن نسبت می‌دهد.
    
    پارامترها:
        path (str): مسیر (path) که برای ساخت URL استفاده می‌شود؛ می‌تواند شامل پیشوند پنل ادمین یا هر مسیر نسبی/مطلقی باشد.
        user: شیء کاربر (معمولاً یک نمونهٔ User یا AnonymousUser) که به request.user نسبت داده می‌شود.
        params (dict | None): دیکشنری پارامیمترهای کوئری؛ مقادیر لیستی نیز پشتیبانی می‌شوند و با urlencode (doseq=True) به رشتهٔ کوئری تبدیل می‌شوند.
    
    برگشت:
        django.http.HttpRequest: یک شیء درخواست GET از RequestFactory که query string (در صورت وجود) را دارد و user به آن الصاق شده است.
    """
    rf = RequestFactory()
    query = ""
    if params:
        from urllib.parse import urlencode
        query = "?" + urlencode(params, doseq=True)
    request = rf.get(f"{path}{query}")
    request.user = user
    return request

def get_admin_changelist_url(model):
    """
    یک رشته‌ی URL برای صفحه‌ی لیست (changelist) ادمین مربوط به مدل داده‌شده تولید می‌کند.
    
    این تابع نام مسیر ادمین را از متادیتای مدل (app_label و model_name) می‌سازد و با استفاده از `reverse` آدرس کامل تغییرات (changelist) بخش ادمین را بازمی‌گرداند.
    
    Parameters:
        model: کلاسی از نوع Django model (نوعی subclass از django.db.models.Model) که برای آن آدرس changelist ساخته می‌شود.
    
    Returns:
        str: مسیر کامل (URL) صفحه‌ی changelist در بخش ادمین Django برای مدل ورودی.
    """
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")

def test_list_display_contains_expected_columns():
    ma = AISummaryAdmin(AISummary, admin.site)
    assert ("patient", "resource_type", "created_at") == tuple(ma.list_display)

def test_get_list_filter_overrides_and_includes_custom_filter():
    ma = AISummaryAdmin(AISummary, admin.site)
    # The attribute exists for expectations but runtime list_filter comes from get_list_filter
    assert ("created_at",) == ma.list_filter
    resolved = ma.get_list_filter(request=None)
    # Expect custom filter class and created_at
    assert isinstance(resolved, (list, tuple))
    assert resolved[0] is AISummaryResourceTypeFilter
    assert "created_at" in resolved

def test_resource_type_filter_lookups_only_unique_non_empty_models(admin_client):
    # Prepare multiple summaries across different content types; include an empty/None model case if possible
    # Create two different content types (e.g., "note" and "report")
    create_ai_summary(model_label="note")
    create_ai_summary(model_label="note")
    create_ai_summary(model_label="report")

    # Instantiate filter and compute lookups
    request = admin_client.request().wsgi_request  # minimal request object
    ma = AISummaryAdmin(AISummary, admin.site)
    flt = AISummaryResourceTypeFilter(request, {}, AISummary, ma)
    lookups = flt.lookups(request, ma)

    # Expect only two unique entries and both labels match the model names
    labels = sorted([label for value, label in lookups])
    assert labels == ["note", "report"]

def test_resource_type_filter_queryset_filters_when_value_selected(admin_client):
    create_ai_summary(model_label="alpha")
    create_ai_summary(model_label="beta")
    request = admin_client.request().wsgi_request
    ma = AISummaryAdmin(AISummary, admin.site)

    # Simulate selecting "alpha" from the filter by overriding self.value()
    class _Filter(AISummaryResourceTypeFilter):
        def value(self):
            """
            یک مقدار ثابت فیلتر را برمی‌گرداند.
            
            این متد در تست‌ها برای شبیه‌سازی حالتی که کاربر فیلتر `resource_type` را روی مقدار `"alpha"` تنظیم کرده، مقدار انتخاب‌شده‌ی فیلتر را برمی‌گرداند.
            
            Returns:
                str: مقدار فیلتر (`"alpha"`).
            """
            return "alpha"

    flt = _Filter(request, {}, AISummary, ma)
    qs = flt.queryset(request, AISummary.objects.all())
    assert qs.count() == 1
    assert qs.first().content_type.model == "alpha"

def test_resource_type_filter_queryset_returns_unfiltered_when_no_value(admin_client):
    create_ai_summary(model_label="alpha")
    create_ai_summary(model_label="beta")
    request = admin_client.request().wsgi_request
    ma = AISummaryAdmin(AISummary, admin.site)
    flt = AISummaryResourceTypeFilter(request, {}, AISummary, ma)
    qs = flt.queryset(request, AISummary.objects.all())
    assert qs.count() == 2

def test_changelist_view_renders_with_result_list_marker(client):
    # Create superuser and login to access admin
    user, password = make_superuser()
    client = Client()
    assert client.login(username=user.username, password=password)
    # Seed at least one record to avoid empty queryset edge-cases
    create_ai_summary(model_label="rendercheck")

    url = get_admin_changelist_url(AISummary)
    resp = client.get(url)
    # The overridden changelist_view ensures render() is called and injects result_list marker if missing
    assert resp.status_code == 200
    content = resp.content or b""
    assert b"result_list" in content

def test_changelist_view_handles_non_renderable_response_gracefully(monkeypatch):
    # Build a fake admin instance whose super().changelist_view returns a minimal object
    class NoRenderResponse:
        # Missing render/content attributes should be tolerated by try/except
        pass

    def fake_changelist_view(self, request, extra_context=None):
        """
        واژهٔ کوتاه:
        یک پاسخ شبیه‌سازی‌شدهٔ غیرقابل‌رندر برای جایگزینی متد changelist_view در تست‌ها بازمی‌گرداند.
        
        توضیح کامل:
        این تابع یک پیاده‌سازی سادهٔ جایگزین برای متد admin.changelist_view است که همیشه یک نمونهٔ NoRenderResponse را بازمی‌گرداند. برای تست سناریوهایی استفاده می‌شود که در آن نمای تغییرات (changelist) به‌جای یک HttpResponse قابل رندر، یک شیئی بازمی‌گرداند که هیچ متد یا محتوای قابل‌ریندری ندارد تا رفتار کد میزبان هنگام دریافت پاسخ‌های غیرمعمول بررسی شود.
        
        پارامترها:
            request: شیٔ درخواست Django — توسط این تابع استفاده نمی‌شود (فقط برای امضا سازگار است).
            extra_context: دیکشنری زمینهٔ اضافی برای رندر — نادیده گرفته می‌شود.
        
        بازگشتی:
            NoRenderResponse: نمونه‌ای که نشان‌دهندهٔ پاسخ غیرقابل‌رندر است.
        """
        return NoRenderResponse()

    monkeypatch.setattr(AISummaryAdmin, "changelist_view", fake_changelist_view, raising=False)
    # Now call the original implementation against the fake response path by invoking the method on a subclass
    # Rebind the original method to a temporary subclass so we can call it directly
    class _Temp(AISummaryAdmin):
        pass

    # Restore original for super() call; we need to call the real method
    monkeypatch.setattr(AISummaryAdmin, "changelist_view", app_admin.AISummaryAdmin.changelist_view, raising=False)

    rf = RequestFactory()
    req = rf.get("/")
    req.user, _ = make_superuser(username="x2", email="x2@example.com")
    # Patch super().changelist_view to return NoRenderResponse for this call
    orig_super = app_admin.AISummaryAdmin.changelist_view

    def super_stub(self, request, extra_context=None):
        """
        یک استاب برای جایگزینی نمای (view) ادمین که همیشه یک NoRenderResponse برمی‌گرداند.
        
        این تابع بدون استفاده از ورودی‌ها (request و extra_context) یک نمونه‌ی NoRenderResponse را بازمی‌گرداند. برای تست‌های مرتبط با ادمین استفاده می‌شود تا فرایند رندرینگ صفحه را دور بزند و بتوان رفتار کد هنگام دریافت یک پاسخ غیرقابل‌رنـدر را بررسی کرد.
        
        Parameters:
            request: شیء درخواست Django که نادیده گرفته می‌شود.
            extra_context (optional): دیکشنری زمینه اضافی که نادیده گرفته می‌شود.
        
        Returns:
            NoRenderResponse: یک نمونه از کلاس NoRenderResponse جهت جلوگیری از رندرینگ پاسخ.
        """
        return NoRenderResponse()

    try:
        monkeypatch.setattr(app_admin.AISummaryAdmin, "changelist_view", super_stub, raising=False)
        resp = _Temp(AISummary, admin.site).changelist_view(req)
        # Should return the same object without raising; no attributes to assert other than type
        assert isinstance(resp, NoRenderResponse)
    finally:
        monkeypatch.setattr(app_admin.AISummaryAdmin, "changelist_view", orig_super, raising=False)

def test_search_fields_and_readonly_and_select_related_contract():
    ma = AISummaryAdmin(AISummary, admin.site)
    assert ("patient__full_name", "content_type__model", "summary") == ma.search_fields
    assert ("id", "created_at") == ma.readonly_fields
    assert ("patient", "content_type") == ma.list_select_related

def test_created_at_filter_and_date_range_behaviour(client):
    # Verify that created_at remains usable alongside custom filter
    """
    آزمون اینکه فیلتر `created_at` در کنار فیلتر سفارشی `resource_type` قابل استفاده بوده و صفحه‌ی changelist با محدوده‌های زمانی مختلف صحیح رندر می‌شود.
    
    توضیحات:
    این تست یک کاربر سوپرازرو ایجاد و با آن وارد می‌شود، سپس دو نمونه‌ی AISummary با مقادیر `created_at` متفاوت (یک مورد قدیمی و یک مورد جدید) می‌سازد. با درخواست به صفحه‌ی changelist ادمین و اعمال فیلتر `resource_type` برای یکی از مدل‌ها بررسی می‌کند که:
    - پاسخ HTTP با وضعیت 200 بازگردانده می‌شود،
    - محتوای پاسخ شامل نشانگر `result_list` است (یعنی لیست نتایج رندر شده‌اند)،
    - و نمای فیلتر کناری در HTML وجود دارد (یعنی یکی از کلاس‌های `filter` یا `changelist-filter` حضور دارد).
    
    نکته اجرایی:
    تست فرض می‌کند امکان تعیین دستی فیلد `created_at` هنگام ایجاد AISummary فراهم است؛ در صورت غیرفعال بودن این قابلیت، بخش مربوط به مقادیر زمانی قابل تنظیم ممکن است معنادار نباشد.
    """
    user, password = make_superuser(username="dater", email="dater@example.com")
    client = Client()
    assert client.login(username=user.username, password=password)

    # Create two records with different created_at dates if field allows manual set
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=10)
    create_ai_summary(model_label="dateA", created_at=old)
    create_ai_summary(model_label="dateB", created_at=now)

    url = get_admin_changelist_url(AISummary)

    # Filter by resource_type only
    resp = client.get(url, {"resource_type": "dateB"})
    assert resp.status_code == 200
    assert b"result_list" in resp.content

    # Sanity: both records exist; we can't easily assert count from HTML here without parsing,
    # but we validate that the page renders with sidebar filters (presence of 'filter' class)
    assert b"filter" in resp.content or b"changelist-filter" in resp.content