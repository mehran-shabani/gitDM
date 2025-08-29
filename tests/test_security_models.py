# Test framework note: Detected pytest/pytest-django.
# Tests below use django.test.TestCase and run under pytest or manage.py test.

import uuid

# Tests use Django's unittest-style TestCase for compatibility with manage.py test
# and pytest runners.
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.apps import apps


def _get_model_by_name(name: str) -> None:
    """
    یک مدل را بر اساس نام کلاس‌ (string) در میان اپ‌های نصب‌شده پیدا و
    برمی‌گرداند.

    به‌طور دقیق‌تر، نام کلاس مدل را می‌پذیرد و تمام مدل‌های ثبت‌شده در
    Django را پیمایش می‌کند تا کلاس مدلی که __name__ آن با مقدار ورودی
    مطابقت دارد بیابد و آن کلاس مدل (نه یک نمونه) را بازگرداند.
    این تابع برای جلوگیری از واردات سخت‌کد‌شده مسیرهای ماژول مفید است
    و امکان استفاده از نام کلاس برای دسترسی به مدل را فراهم می‌کند.

    Parameters:
        name (str): نام کلاس مدل مورد نظر (مثلاً "AuditLog" یا "Role").

    Returns:
        type: کلاس مدل پیدا شده.

    Raises:
        LookupError: اگر هیچ مدلی با نام داده‌شده در اپ‌های نصب‌شده یافت
            نشود.
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
            user_id=uid,
        )
        self.assertEqual(log.user_id, uid)

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
        # JSONField(default=dict) should create a fresh dict per instance
        """
        بررسی می‌کند که مقدار پیش‌فرض فیلد JSONField (`meta`) برای هر
        نمونه جداگانه است
        و بین نمونه‌ها به اشتراک گذاشته نمی‌شود.

        آزمایش برای اطمینان از این که هر بار که یک AuditLog جدید با مقدار
        پیش‌فرض `meta` ایجاد می‌شود،
        یک دیکشنری جدید ساخته می‌شود (و نه ارجاع به یک شیء مشترک).
        با ایجاد دو نمونه، تغییر در `meta` نمونهٔ اول ذخیره و سپس نمونهٔ دوم
        از دیتابیس تازه‌سازی می‌شود
        تا تضمین شود `meta` آن همچنان یک دیکشنری خالی است.
        """
        log1 = AuditLog.objects.create(
            path="/l1",
            method="GET",
            status_code=200,
        )
        log2 = AuditLog.objects.create(
            path="/l2",
            method="GET",
            status_code=200,
        )

        # Mutate meta on the first log only
        log1.meta["foo"] = "bar"
        log1.save(update_fields=["meta"])

        # Ensure the second instance's meta remains unaffected (fresh default)
        log2.refresh_from_db()
        self.assertEqual(log2.meta, {})


class RoleModelTests(TestCase):
    def setUp(self) -> None:
        """
        یک نمونه‌ی کاربری تستی با نام کاربری "alice" ایجاد می‌کند
        و در self.user قرار می‌دهد.

        این متد برای آماده‌سازی پیش‌شرط‌های تست‌های مربوط به مدل Role اجرا
        می‌شود.
        کاربر ایجاد شده با رمز عبور "pwd12345" ساخته می‌شود و برای وابستگی‌هایی
        که نیاز به یک User واقعی دارند (مثلاً ایجاد یا حذف نقش‌ها و بررسی
        رفتار یک‌به‌یک یا cascade) استفاده می‌شود.
        """
        self.user = User.objects.create_user(
            username="alice", password="pwd12345"
        )

    def test_role_creation_and_uuid_primary_key(self) -> None:
        r = Role.objects.create(user=self.user, role="admin")
        # id is a UUIDField primary key
        self.assertIsInstance(r.id, uuid.UUID)
        self.assertEqual(r.role, "admin")
        self.assertEqual(str(r.user.username), "alice")

    def test_role_choices_accept_only_defined_values(self) -> None:
        # Valid choices: admin, doctor, viewer
        for choice in ("admin", "doctor", "viewer"):
            with self.subTest(choice=choice):
                u = User.objects.create_user(
                    username=f"user_{choice}", password="x"
                )
                instance = Role(user=u, role=choice)
                # Should validate successfully
                instance.full_clean()
                instance.save()
                self.assertEqual(instance.role, choice)

    def test_invalid_role_choice_raises_validation_error(self) -> None:
        u = User.objects.create_user(username="bob", password="pwd")
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


# ---------------------------------------------------------------------------
# Additional tests appended: focus on happy paths, boundaries, and failures.
# Framework: pytest + pytest-django, using Django's TestCase.
# ---------------------------------------------------------------------------


class AuditLogModelAdditionalTests(TestCase):
    def test_path_max_length_boundary_allows_200(self) -> None:
        # Boundary: exactly 200 chars should be valid
        path_ok = "/" + "a" * 199
        log = AuditLog(path=path_ok, method="GET", status_code=204)
        log.full_clean()  # should not raise
        log.save()
        self.assertEqual(log.path, path_ok)

    def test_method_max_length_boundary_allows_10(self) -> None:
        # Boundary: exactly 10 chars should be valid
        method_ok = "X" * 10
        log = AuditLog(path="/ok-boundary", method=method_ok, status_code=200)
        log.full_clean()  # should not raise
        log.save()
        self.assertEqual(log.method, method_ok)

    def test_user_id_invalid_string_raises_validation_error(self) -> None:
        # Invalid UUID format should fail validation
        log = AuditLog(
            path="/bad-uuid",
            method="GET",
            status_code=200,
            user_id="not-a-uuid",
        )
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_meta_nested_round_trip_persists_structure(self) -> None:
        # JSONField should persist nested structures losslessly
        payload = {"a": 1, "b": [1, 2, {"c": "d"}], "e": {"f": True, "g": None}}
        created = AuditLog.objects.create(
            path="/nested",
            method="POST",
            status_code=201,
            meta=payload,
        )
        fetched = AuditLog.objects.get(pk=created.pk)
        self.assertEqual(fetched.meta, payload)

    def test_meta_non_serializable_raises_type_error_on_save(self) -> None:
        # Sets are not JSON-serializable.
        # Saving should raise TypeError during serialization
        with self.assertRaises(TypeError):
            AuditLog.objects.create(
                path="/bad-meta",
                method="GET",
                status_code=200,
                meta={"invalid": {1, 2}},
            )


class RoleModelAdditionalTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="charlie", password="pwd12345")

    def test_user_reverse_one_to_one_relation_returns_role(self) -> None:
        r = Role.objects.create(user=self.user, role="viewer")
        # Access via reverse OneToOne relation
        self.assertEqual(self.user.role.pk, r.pk)

    def test_deleting_role_does_not_delete_user(self) -> None:
        r = Role.objects.create(user=self.user, role="admin")
        r.delete()
        # User should remain after Role deletion
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_multiple_users_can_have_distinct_roles(self) -> None:
        u2 = User.objects.create_user(username="dana", password="x")
        r1 = Role.objects.create(user=self.user, role="admin")
        r2 = Role.objects.create(user=u2, role="doctor")
        self.assertEqual(Role.objects.count(), 2)
        self.assertEqual(Role.objects.get(user=self.user).role, "admin")
        self.assertEqual(Role.objects.get(user=u2).role, "doctor")
        # Sanity: ids are UUIDs
        self.assertIsInstance(r1.id, uuid.UUID)
        self.assertIsInstance(r2.id, uuid.UUID)

    def test_update_existing_role_value_validates_and_saves(self) -> None:
        r = Role.objects.create(user=self.user, role="viewer")
        r.role = "doctor"
        # Should validate for allowed choice and persist
        r.full_clean()
        r.save(update_fields=["role"])
        self.assertEqual(Role.objects.get(pk=r.pk).role, "doctor")

    def test_invalid_role_choice_case_sensitivity(self) -> None:
        u = User.objects.create_user(username="erin", password="x")
        instance = Role(user=u, role="ADMIN")  # likely invalid if choices are lowercase
        with self.assertRaises(ValidationError):
            instance.full_clean()