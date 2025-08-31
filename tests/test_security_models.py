# Test framework note: Detected pytest/pytest-django.
# Tests below use django.test.TestCase and run under pytest or manage.py test.

import uuid

# Tests use Django's unittest-style TestCase for compatibility with manage.py test
# and pytest runners.
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.apps import apps


User = get_user_model()

def _get_model_by_name(name: str) -> None:
    """
    یک مدل را بر اساس نام کلاس‌ (string) در میان اپ‌های نصب‌شده پیدا و برمی‌گرداند.
    
    به‌طور دقیق‌تر، نام کلاس مدل را می‌پذیرد و تمام مدل‌های ثبت‌شده در Django را پیمایش می‌کند تا کلاس مدلی که __name__ آن با مقدار ورودی مطابقت دارد بیابد و آن کلاس مدل (نه یک نمونه) را بازگرداند. این تابع برای جلوگیری از واردات سخت‌کد‌شده مسیرهای ماژول مفید است و امکان استفاده از نام کلاس برای دسترسی به مدل را فراهم می‌کند.
    
    Parameters:
        name (str): نام کلاس مدل مورد نظر (مثلاً "AuditLog" یا "Role").
    
    Returns:
        type: کلاس مدل پیدا شده.
    
    Raises:
        LookupError: اگر هیچ مدلی با نام داده‌شده در اپ‌های نصب‌شده یافت نشود.
    """
    for model in apps.get_models():
        if model.__name__ == name:
            return model
    raise LookupError(f"Model '{name}' not found in installed apps")


# Resolve models dynamically to avoid guessing module paths
AuditLog = _get_model_by_name("AuditLog")
Role = _get_model_by_name("Role")


class AuditLogModelTests(TestCase):
    def test_creation_with_defaults(self) -> None:
        log = AuditLog.objects.create(
            path="/api/resource",
            method="GET",
            status_code=200,
        )
        # id should be an integer (BigAutoField), created_at is auto-populated,
        # user_id is nullable, and meta defaults to a new empty dict.
        self.assertIsInstance(log.id, int)
        self.assertIsNotNone(log.created_at)
        self.assertIsNone(log.user_id)
        self.assertEqual(log.meta, {})
        self.assertEqual(log.path, "/api/resource")
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.status_code, 200)

    def test_user_id_accepts_uuid(self) -> None:
        uid = uuid.uuid4()
        log = AuditLog.objects.create(
            path="/submit",
            method="POST",
            status_code=201,
            user_id=str(uid),
        )
        self.assertEqual(str(log.user_id), str(uid))

    def test_path_max_length_validation(self) -> None:
        # max_length for path is 200; 201 should fail on full_clean
        long_path = "/" + "a" * 201
        log = AuditLog(path=long_path, method="GET", status_code=200)
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_method_max_length_validation(self) -> None:
        # max_length for method is 10; 11 should fail on full_clean
        long_method = "X" * 11
        log = AuditLog(path="/ok", method=long_method, status_code=200)
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_meta_default_is_not_shared_between_instances(self) -> None:
        """
        بررسی می‌کند که مقدار پیش‌فرض فیلد JSONField (`meta`) برای هر نمونه جداگانه است و بین نمونه‌ها به اشتراک گذاشته نمی‌شود.
        
        آزمایش برای اطمینان از این که هر بار که یک AuditLog جدید با مقدار پیش‌فرض `meta` ایجاد می‌شود، یک دیکشنری جدید ساخته می‌شود (و نه ارجاع به یک شیء مشترک). با ایجاد دو نمونه، تغییر در `meta` نمونهٔ اول ذخیره و سپس نمونهٔ دوم از دیتابیس تازه‌سازی می‌شود تا تضمین شود `meta` آن همچنان یک دیکشنری خالی است.
        """
        log1 = AuditLog.objects.create(path="/l1", method="GET", status_code=200)
        log2 = AuditLog.objects.create(path="/l2", method="GET", status_code=200)

        # Mutate meta on the first log only
        log1.meta["foo"] = "bar"
        log1.save(update_fields=["meta"])

        # Ensure the second instance's meta remains unaffected (fresh default)
        log2.refresh_from_db()
        self.assertEqual(log2.meta, {})


class RoleModelTests(TestCase):
    def setUp(self) -> None:
        """
        یک نمونه‌ی کاربری تستی با نام کاربری "alice" ایجاد می‌کند و در self.user قرار می‌دهد.
        
        این متد برای آماده‌سازی پیش‌شرط‌های تست‌های مربوط به مدل Role اجرا می‌شود. کاربر ایجاد شده با رمز عبور "pwd12345" ساخته می‌شود و برای وابستگی‌هایی که نیاز به یک User واقعی دارند (مثلاً ایجاد یا حذف نقش‌ها و بررسی رفتار یک‌به‌یک یا cascade) استفاده می‌شود.
        """
        self.user = User.objects.create_user(email="alice@example.com", password="pwd12345")

    def test_role_creation_and_uuid_primary_key(self) -> None:
        r = Role.objects.create(user=self.user, role="admin")
        # id is an integer (BigAutoField)
        self.assertIsInstance(r.id, int)
        self.assertEqual(r.role, "admin")
        self.assertEqual(str(self.user.email), "alice@example.com")

    def test_role_choices_accept_only_defined_values(self) -> None:
        # Valid choices: admin, doctor, viewer
        for choice in ("admin", "doctor", "viewer"):
            with self.subTest(choice=choice):
                u = User.objects.create_user(email=f"user_{choice}@example.com", password="x")
                instance = Role(user=u, role=choice)
                # Should validate successfully
                instance.full_clean()
                instance.save()
                self.assertEqual(instance.role, choice)

    def test_invalid_role_choice_raises_validation_error(self) -> None:
        u = User.objects.create_user(email="bob@example.com", password="pwd")
        instance = Role(user=u, role="invalid")
        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_one_to_one_constraint_prevents_duplicate_roles_for_same_user(self) -> None:
        Role.objects.create(user=self.user, role="viewer")
        # Creating another role for the same user must violate the OneToOne constraint
        with self.assertRaises(IntegrityError):
            Role.objects.create(user=self.user, role="doctor")

    def test_cascade_delete_on_user_removes_role(self) -> None:
        r = Role.objects.create(user=self.user, role="viewer")
        # Deleting the user should cascade and delete the Role
        self.user.delete()
        self.assertFalse(Role.objects.filter(pk=r.pk).exists())