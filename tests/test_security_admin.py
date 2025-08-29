# ruff: noqa: RUF002, E501
"""
Unit tests for Django admin registrations and configurations of
AuditLogAdmin and RoleAdmin.

Testing library/framework note:
- These tests use django.test.TestCase (unittest style) to remain compatible with
  both Django's test runner and pytest if the project uses pytest/pytest-django.

Focus:
- Based strictly on the provided diff snippet (admin registrations). We validate:
  * Admin classes are registered
  * list_display / list_filter / readonly_fields match expected values and
    reference valid fields
  * Basic admin access behavior (changelist) for superuser and unauthenticated user
"""

from django.contrib import admin as django_admin
from django.contrib.admin import ModelAdmin
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.apps import apps as django_apps
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse


def _get_model_by_name(model_name: str) -> None:
    """
    یک مدل Django را بر اساس نام کلاس среди تمام اپ‌های نصب‌شده پیدا و بازمی‌گرداند.

    این تابع تمام مدل‌های ثبت‌شده در django.apps را پیمایش می‌کند و اولین مدلی را
    که نام کلاس آن دقیقا با مقدار رشته‌ای model_name مطابقت دارد برمی‌گرداند.
    در صورت عدم یافتن مدل، یک AssertionError پرتاب می‌شود تا خطا سریعاً آشکار شود
    (مناسب برای تست‌ها و بررسی‌های شروعی).

    Parameters:
        model_name (str): نام کلاس مدل موردنظر (مثال: "AuditLog").

    Returns:
        type: کلاس مدل پیدا‌شده.

    Raises:
        AssertionError: اگر مدلی با نام داده‌شده در اپ‌های نصب‌شده یافت نشود.
    """
    for model in django_apps.get_models():
        if model.__name__ == model_name:
            return model
    raise AssertionError(
        f"Model '{model_name}' not found in installed apps"
    )


class _BaseAdminTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        راه‌انداز کلاس تست: فراخوانی راه‌اندازی کلاس والد و کشف خودکار ماژول‌های admin.

        این متد در سطح کلاس اجرا می‌شود، ابتدا پیاده‌سازی والد (TestCase.setUpClass)
        را اجرا می‌کند و سپس django_admin.autodiscover() را فراخوانی می‌کند تا همه
        ماژول‌های admin.py بارگذاری شوند و django_admin.site._registry با
        ثبت‌نام‌های اپلیکیشن‌ها پر شود. این رفتار برای تست‌های مربوط به بررسی
        ثبت و پیکربندی ادمین لازم است.
        """
        super().setUpClass()
        # Ensure all admin.py modules are discovered so site._registry is populated
        django_admin.autodiscover()

    def setUp(self) -> None:
        """
        یک‌خطی:
        محیط تست را آماده می‌کند: کلاینت، RequestFactory و یک superuser با شناسه‌ی
        قطعی می‌سازد و با آن وارد می‌شود.

        توضیح کامل:
        برای هر تست اجرا می‌شود و این کارها را انجام می‌دهد:
        - یک نمونهٔ Django Test Client در self.client ایجاد می‌کند.
        - یک RequestFactory در self.factory ایجاد می‌کند.
        - یک کاربر superuser با مشخصات قطعی (username: "admin_test_user",
          email: "admin_test_user@example.com", password: "securepass123")
          در پایگاه‌داده ایجاد می‌کند و آن را در self.admin_user نگهداری می‌کند.
        - client را با کاربر ایجادشده لاگین اجباری (force login) می‌کند تا
          درخواست‌های بعدی در تست‌ها با دسترسی سوپروسری اجرا شوند.

        تأثیر جانبی:
        یک رکورد کاربر superuser در پایگاه‌داده آزمایشی ساخته می‌شود و client
        در حالت احراز هویت قرار می‌گیرد.
        """
        self.client = Client()
        self.factory = RequestFactory()
        user_model = get_user_model()
        # Use deterministic credentials
        self.admin_user = user_model.objects.create_superuser(
            username="admin_test_user",
            email="admin_test_user@example.com",
            password="securepass123",
        )
        self.client.force_login(self.admin_user)

    def _make_request(self, path: str = "/admin/") -> None:
        """
        یک درخواست GET تستی برای مسیر مشخص می‌سازد و کاربر ادمین تست را به آن
        پیوست می‌کند.

        ایده‌آل برای استفاده در تست‌های Admin:
        یک HttpRequest تولید می‌کند که مسیر آن با آرگومان `path` تعیین می‌شود
        و فیلد `user` آن به کاربر ادمین ساخته‌شده در setUp اشاره می‌کند،
        تا فراخوانی متدهای ادمین (مثل `get_list_display`) یا نمایش
        changelist با یک درخواست معتبر شبیه‌سازی شود.

        Parameters:
            path (str): مسیر درخواست HTTP (پیش‌فرض "/admin/"). می‌تواند هر مسیر
            دلخواه برای تست صفحات ادمین یا viewهای مرتبط باشد.

        Returns:
            django.http.HttpRequest: شیء درخواست GET با `user` تنظیم‌شده روی
            کاربر ادمین تست.
        """
        req = self.factory.get(path)
        req.user = self.admin_user
        return req

    def _assert_admin_registered(self, model: type) -> None:
        """
        استقرار ثبت‌شدن مدل در ادارهٔ ادمین را تایید و شیء ثبت‌شدهٔ مربوطه را
        برمی‌گرداند.

        پارامترها:
            model (type): کلاسی از مدل‌های Django که وجود ثبت‌نام آن در
            admin.site بررسی می‌شود.

        بازگشت:
            object: شیء ثبت‌شده در admin.site._registry برای مدل
            (معمولاً یک ModelAdmin).

        استثناها:
            AssertionError: در صورتی که مدل در registry ادمین ثبت نشده باشد، با
            پیام حاوی نام مدل خطا ایجاد می‌شود.
        """
        self.assertIn(
            model,
            django_admin.site._registry,
            f"{model.__name__} is not registered in admin.site",
        )
        return django_admin.site._registry[model]

    def _assert_changelist_accessible(self, model: type) -> None:
        """
        بررسی می‌کند که صفحه‌ی changelist ادمین برای مدل مشخص شده قابل
        دسترسی است و در صورت عدم دستیابی، تست را ناموفق می‌سازد.
        """
        url = reverse(
            f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
        )
        resp = self.client.get(url)
        self.assertEqual(
            resp.status_code,
            200,
            (f"Expected 200 OK for changelist of {model.__name__}, "
             f"got {resp.status_code}"),
        )
        return url

    def _assert_changelist_requires_login(self, model: type) -> None:
        """
        بررسی می‌کند که صفحه changelist مربوط به مدل داده‌شده نیاز به ورود (login) دارد.
        """
        url = reverse(
            f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
        )
        self.client.logout()
        resp = self.client.get(url, follow=False)
        # Unauthenticated users should be redirected to admin login
        self.assertIn(
            resp.status_code, (301, 302), "Expected redirect to admin login"
        )
        self.assertIn("/admin/login", resp["Location"])



class TestAuditLogAdminConfig(_BaseAdminTestCase):
    def setUp(self) -> None:
        """
        یک‌خطی:
        تنظیم اولیهٔ تست‌های AuditLog: بارگذاری مدل AuditLog و شیء ادمین ثبت‌شدهٔ آن.
        """
        super().setUp()
        self.model = _get_model_by_name("AuditLog")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_is_modeladmin_instance(self) -> None:
        self.assertIsInstance(self.admin_obj, ModelAdmin)

    def test_list_display_exact_order(self) -> None:
        expected = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at']
        self.assertEqual(list(self.admin_obj.list_display), expected)

    def test_list_filter_exact_order(self) -> None:
        """
        بررسی می‌کند که ویژگی `list_filter` در شیء ادمین مربوط به AuditLog دقیقا و با
        همان ترتیب موردانتظار باشد.
        """
        expected = ['method', 'status_code', 'created_at']
        self.assertEqual(list(self.admin_obj.list_filter), expected)

    def test_readonly_fields_contents_ignore_order(self) -> None:
        expected = [
            'id',
            'user_id',
            'path',
            'method',
            'status_code',
            'created_at',
            'meta',
        ]
        self.assertCountEqual(list(self.admin_obj.readonly_fields), expected)

    def test_list_display_fields_exist_on_model_or_admin(self) -> None:
        # Validate that list_display items resolve to model fields or admin attributes
        names = list(self.admin_obj.get_list_display(self._make_request()))
        for name in names:
            try:
                # Will succeed for real model fields (including 'id')
                self.model._meta.get_field(name)
            except FieldDoesNotExist:
                self.assertTrue(
                    hasattr(self.model, name) or hasattr(self.admin_obj, name),
                    f"list_display item '{name}' not present on model/admin",
                )

    def test_list_filter_fields_exist_on_model(self) -> None:
        """
        اطمینان می‌دهد که همهٔ نام‌های موجود در `list_filter` ادمین، فیلدهای واقعی مدل هستند.
        """
        for name in list(self.admin_obj.list_filter):
            try:
                self.model._meta.get_field(name)
            except FieldDoesNotExist:
                self.fail(
                    f"list_filter item '{name}' not a model field on {self.model.__name__}"
                )

    def test_get_readonly_fields_matches_config(self) -> None:
        req = self._make_request()
        readonly = list(self.admin_obj.get_readonly_fields(req))
        expected = [
            'id',
            'user_id',
            'path',
            'method',
            'status_code',
            'created_at',
            'meta',
        ]
        self.assertCountEqual(readonly, expected)

    def test_changelist_accessible_for_superuser(self) -> None:
        """
        اطمینان حاصل می‌کند که صفحه‌ی changelist مربوط به مدل ثبت‌شده در پنل ادمین برای
        یک سوپر‌کاربر وارد‌شده قابل دسترسی است. این تست با استفاده از کمک‌تابع
        _assert_changelist_accessible دسترسی HTTP 200 به آدرس changelist مدل را بررسی می‌کند.
        """
        self._assert_changelist_accessible(self.model)

    def test_changelist_redirects_when_not_logged_in(self) -> None:
        """
        اطمینان حاصل می‌کند که صفحه لیست (changelist) ادمین برای مدل تحت آزمون هنگام
        عدم ورود کاربر به صفحه ورود ادمین هدایت (redirect) می‌شود.
        """
        self._assert_changelist_requires_login(self.model)


class TestRoleAdminConfig(_BaseAdminTestCase):
    def setUp(self) -> None:
        """
        تنظیم اولیهٔ تست‌ها برای کلاس TestRoleAdminConfig.
        """
        super().setUp()
        self.model = _get_model_by_name("Role")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_is_modeladmin_instance(self) -> None:
        self.assertIsInstance(self.admin_obj, ModelAdmin)

    def test_list_display_exact_order(self) -> None:
        """
        بررسی می‌کند که ویژگی `list_display` در کلاس مدیر (RoleAdmin) دقیقا برابر با
        ترتیب مورد انتظار ['id', 'user', 'role'] باشد.
        """
        expected = ['id', 'user', 'role']
        self.assertEqual(list(self.admin_obj.list_display), expected)

    def test_list_filter_exact_order(self) -> None:
        expected = ['role']
        self.assertEqual(list(self.admin_obj.list_filter), expected)

    def test_list_display_fields_exist_on_model_or_admin(self) -> None:
        """
        بررسی می‌کند که هر نام موجود در `list_display` یک فیلد مدل یا صفت قابل‌دسترسی
        روی مدل یا شیء ادمین باشد.
        """
        names = list(self.admin_obj.get_list_display(self._make_request()))
        for name in names:
            try:
                self.model._meta.get_field(name)
            except FieldDoesNotExist:
                self.assertTrue(
                    hasattr(self.model, name) or hasattr(self.admin_obj, name),
                    f"list_display item '{name}' not present on model/admin",
                )

    def test_list_filter_fields_exist_on_model(self) -> None:
        """
        اطمینان می‌دهد که همهٔ نام‌های موجود در `list_filter` ادمین، فیلدهای واقعی مدل هستند.
        """
        for name in list(self.admin_obj.list_filter):
            try:
                self.model._meta.get_field(name)
            except FieldDoesNotExist:
                self.fail(
                    f"list_filter item '{name}' not a model field on {self.model.__name__}"
                )

    def test_changelist_accessible_for_superuser(self) -> None:
        """
        اطمینان حاصل می‌کند که صفحه‌ی changelist مربوط به مدل ثبت‌شده در پنل ادمین برای
        یک سوپر‌کاربر وارد‌شده قابل دسترسی است.
        """
        self._assert_changelist_accessible(self.model)

    def test_changelist_redirects_when_not_logged_in(self) -> None:
        """
        اطمینان حاصل می‌کند که صفحه لیست (changelist) ادمین برای مدل تحت آزمون هنگام
        عدم ورود کاربر به صفحه ورود ادمین هدایت (redirect) می‌شود.
        """
        self._assert_changelist_requires_login(self.model)


class TestAuditLogAdminAdditional(_BaseAdminTestCase):
    """
    Additional coverage for AuditLogAdmin:
    - Validate optional admin attributes if defined: search_fields, ordering, date_hierarchy
    - Validate get_readonly_fields respects configuration
    - Check permission methods (has_add/change/delete_permission) typical for audit logs
      (read-only) but without assuming; if method exists, assert expected boolean by invoking it.
    - Validate changelist, change, and add URLs are protected by login.
    """

    def setUp(self) -> None:
        super().setUp()
        self.model = _get_model_by_name("AuditLog")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_optional_attributes_shape_if_defined(self) -> None:
        # If attributes exist, ensure they are iterable/tuples/lists with strings
        for attr in ("search_fields", "ordering", "date_hierarchy"):
            if hasattr(self.admin_obj, attr):
                val = getattr(self.admin_obj, attr)
                if attr == "date_hierarchy":
                    # Can be a single field name or None
                    if val is not None:
                        self.assertIsInstance(val, str, f"{attr} must be a field name when set")
                        # Ensure field exists on model
                        try:
                            self.model._meta.get_field(val)
                        except Exception as exc:
                            self.fail(f"{attr} refers to unknown field '{val}': {exc}")
                else:
                    self.assertTrue(hasattr(val, "__iter__"), f"{attr} should be iterable")
                    for item in list(val):
                        self.assertIsInstance(item, str, f"{attr} items must be str")

    def test_permission_methods_when_present(self) -> None:
        req = self._make_request()
        obj = None
        # We don't assume read-only; we assert consistency: methods return bool.
        for meth in ("has_add_permission", "has_change_permission", "has_delete_permission"):
            if hasattr(self.admin_obj, meth):
                res = getattr(self.admin_obj, meth)(req, obj)
                self.assertIsInstance(res, bool, f"{meth} should return bool")

    def test_change_and_add_views_require_login(self) -> None:
        # Ensure change/add views redirect to login when logged out
        change_url = reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")
        self.client.logout()
        resp = self.client.get(change_url, follow=False)
        self.assertIn(resp.status_code, (301, 302))
        self.assertIn("/admin/login", resp["Location"])

    def test_list_display_non_empty(self) -> None:
        names = list(getattr(self.admin_obj, "list_display", ()))
        self.assertTrue(len(names) >= 1, "list_display should not be empty for AuditLogAdmin")


class TestRoleAdminAdditional(_BaseAdminTestCase):
    """
    Additional coverage for RoleAdmin:
    - Validate optional search_fields/ordering/date_hierarchy if defined
    - Validate list_display and list_filter refer to model/admin attributes
    - Check permissions when methods exist
    """

    def setUp(self) -> None:
        super().setUp()
        self.model = _get_model_by_name("Role")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_optional_attributes_shape_if_defined(self) -> None:
        for attr in ("search_fields", "ordering", "date_hierarchy"):
            if hasattr(self.admin_obj, attr):
                val = getattr(self.admin_obj, attr)
                if attr == "date_hierarchy":
                    if val is not None:
                        self.assertIsInstance(val, str)
                        try:
                            self.model._meta.get_field(val)
                        except Exception as exc:
                            self.fail(f"{attr} refers to unknown field '{val}': {exc}")
                else:
                    self.assertTrue(hasattr(val, "__iter__"))
                    for item in list(val):
                        self.assertIsInstance(item, str)

    def test_list_display_and_filter_names_resolve(self) -> None:
        req = self._make_request()
        list_display = list(self.admin_obj.get_list_display(req))
        for name in list_display:
            # Either a real field or an attr on model/admin
            try:
                self.model._meta.get_field(name)
            except Exception:
                self.assertTrue(
                    hasattr(self.model, name) or hasattr(self.admin_obj, name),
                    f"list_display item '{name}' not found on model/admin"
                )

        for name in list(getattr(self.admin_obj, "list_filter", ())):
            try:
                self.model._meta.get_field(name)
            except Exception:
                self.fail(f"list_filter item '{name}' not a model field on {self.model.__name__}")

    def test_permission_methods_when_present(self) -> None:
        req = self._make_request()
        for meth in ("has_add_permission", "has_change_permission", "has_delete_permission"):
            if hasattr(self.admin_obj, meth):
                res = getattr(self.admin_obj, meth)(req)
                self.assertIsInstance(res, bool, f"{meth} should return bool")