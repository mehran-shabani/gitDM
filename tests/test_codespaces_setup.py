"""Test to verify GitHub Codespaces setup is working correctly."""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.conf import settings


class CodespacesSetupTest(TestCase):
    """Basic tests to verify the Codespaces environment is properly configured."""
    
    def test_settings_loaded(self):
        """Test that Django settings are properly loaded."""
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsNotNone(settings.DATABASES)
    
    def test_health_endpoint(self):
        """Test that the health endpoint is accessible."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
    
    def test_admin_url_accessible(self):
        """Test that admin URL is accessible (though login required)."""
        response = self.client.get('/admin/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_api_schema_accessible(self):
        """Test that API schema endpoint is accessible."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)


@pytest.mark.django_db
def test_database_connection():
    """Test that database connection works."""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1