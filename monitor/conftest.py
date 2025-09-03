"""Pytest configuration for monitor app tests."""

import pytest
from django.test import override_settings


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture
def celery_settings():
    """Override Celery settings for testing."""
    return {
        'task_always_eager': True,
        'task_eager_propagates': True,
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
    }


@pytest.fixture
def mock_openai_settings():
    """Mock OpenAI settings for testing."""
    with override_settings(OPENAI_API_KEY='test-key'):
        yield


@pytest.fixture
def no_openai_settings():
    """Remove OpenAI settings for testing fallback."""
    with override_settings(OPENAI_API_KEY=None):
        yield