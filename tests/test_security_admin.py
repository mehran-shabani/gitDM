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
    Resolve a model by class name across all installed apps.
    Raises AssertionError if not found to fail fast.
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
        super().setUpClass()
        # Ensure all admin.py modules are discovered so site._registry is populated
        django_admin.autodiscover()

    def setUp(self) -> None:
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
        req = self.factory.get(path)
        req.user = self.admin_user
        return req

    def _assert_admin_registered(self, model: type) -> None:
        self.assertIn(
            model,
            django_admin.site._registry,
            f"{model.__name__} is not registered in admin.site",
        )
        return django_admin.site._registry[model]

    def _assert_changelist_accessible(self, model: type) -> None:
        url = reverse(
            f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
        )
        resp = self.client.get(url)
        self.assertEqual(
            resp.status_code,
            200,
            f"Expected 200 OK for changelist of {model.__name__}, got {resp.status_code}",
        )
        return url

    def _assert_changelist_requires_login(self, model: type) -> None:
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
        super().setUp()
        self.model = _get_model_by_name("AuditLog")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_is_modeladmin_instance(self) -> None:
        self.assertIsInstance(self.admin_obj, ModelAdmin)

    def test_list_display_exact_order(self) -> None:
        expected = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at']
        self.assertEqual(list(self.admin_obj.list_display), expected)

    def test_list_filter_exact_order(self) -> None:
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
        self._assert_changelist_accessible(self.model)

    def test_changelist_redirects_when_not_logged_in(self) -> None:
        self._assert_changelist_requires_login(self.model)


class TestRoleAdminConfig(_BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.model = _get_model_by_name("Role")
        self.admin_obj = self._assert_admin_registered(self.model)

    def test_is_modeladmin_instance(self) -> None:
        self.assertIsInstance(self.admin_obj, ModelAdmin)

    def test_list_display_exact_order(self) -> None:
        expected = ['id', 'user', 'role']
        self.assertEqual(list(self.admin_obj.list_display), expected)

    def test_list_filter_exact_order(self) -> None:
        expected = ['role']
        self.assertEqual(list(self.admin_obj.list_filter), expected)

    def test_list_display_fields_exist_on_model_or_admin(self) -> None:
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
        for name in list(self.admin_obj.list_filter):
            try:
                self.model._meta.get_field(name)
            except FieldDoesNotExist:
                self.fail(
                    f"list_filter item '{name}' not a model field on {self.model.__name__}"
                )

    def test_changelist_accessible_for_superuser(self) -> None:
        self._assert_changelist_accessible(self.model)

    def test_changelist_redirects_when_not_logged_in(self) -> None:
        self._assert_changelist_requires_login(self.model)