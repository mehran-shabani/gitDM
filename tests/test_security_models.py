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
    Resolve a model by its class name across installed apps.
    Avoids hard-coding import paths for portability across projects.
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
        self.user = User.objects.create_user(username="alice", password="pwd12345")

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
                u = User.objects.create_user(username=f"user_{choice}", password="x")
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
# Note: pytest + pytest-django; tests use Django's unittest-style TestCase.

class AuditLogModelMoreTests(TestCase):
    """
    Additional coverage for AuditLog model focusing on JSON persistence,
    UUID handling, bulk operations, and partial updates.
    """

    def test_user_id_accepts_string_uuid(self) -> None:
        uid = uuid.uuid4()
        log = AuditLog.objects.create(
            path="/string-uuid",
            method="GET",
            status_code=200,
            user_id=str(uid),
        )
        # UUIDField should coerce string input to UUID
        self.assertEqual(log.user_id, uid)
        fetched = AuditLog.objects.get(pk=log.pk)
        self.assertEqual(fetched.user_id, uid)

    def test_meta_persists_nested_data(self) -> None:
        payload = {
            "ip": "127.0.0.1",
            "headers": {"X-Foo": "Bar"},
            "list": [1, "a", True],
        }
        log = AuditLog.objects.create(
            path="/meta-nested",
            method="POST",
            status_code=201,
            meta=payload,
        )
        log.refresh_from_db()
        self.assertEqual(log.meta, payload)

    def test_bulk_create_and_meta_defaults(self) -> None:
        records = [
            AuditLog(path="/b1", method="GET", status_code=200),
            AuditLog(path="/b2", method="POST", status_code=201),
            AuditLog(path="/b3", method="DELETE", status_code=204),
        ]
        AuditLog.objects.bulk_create(records)
        qs = AuditLog.objects.filter(path__in=["/b1", "/b2", "/b3"]).order_by("path")
        self.assertEqual(qs.count(), 3)
        for rec in qs:
            self.assertEqual(rec.meta, {})

    def test_partial_update_fields_and_refresh(self) -> None:
        log = AuditLog.objects.create(path="/upd", method="GET", status_code=200)
        # Update integer field only
        log.status_code = 404
        log.save(update_fields=["status_code"])
        log.refresh_from_db()
        self.assertEqual(log.status_code, 404)

        # Update JSON field only
        new_meta = {"updated": True, "via": "partial"}
        log.meta = new_meta
        log.save(update_fields=["meta"])
        log.refresh_from_db()
        self.assertEqual(log.meta, new_meta)


class RoleModelMoreTests(TestCase):
    """
    Additional coverage for Role model focusing on validation strictness,
    relational behavior, and multi-user scenarios.
    """

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(username="role_u1", password="p")
        self.user2 = User.objects.create_user(username="role_u2", password="p")

    def test_blank_role_rejected_by_validation(self) -> None:
        instance = Role(user=self.user1, role="")
        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_role_choice_is_case_sensitive_invalid_capitalization(self) -> None:
        # Capitalized should be invalid if choices are lowercase
        instance = Role(user=self.user1, role="Admin")
        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_deleting_role_does_not_delete_user(self) -> None:
        r = Role.objects.create(user=self.user1, role="viewer")
        r.delete()
        # User should remain
        self.assertTrue(User.objects.filter(pk=self.user1.pk).exists())

    def test_same_role_for_different_users_allowed(self) -> None:
        r1 = Role.objects.create(user=self.user1, role="doctor")
        r2 = Role.objects.create(user=self.user2, role="doctor")
        self.assertEqual(r1.role, "doctor")
        self.assertEqual(r2.role, "doctor")
        self.assertNotEqual(r1.user_id, r2.user_id)