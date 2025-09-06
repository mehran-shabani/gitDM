"""
Tests for API views.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from model_bakery import baker

from monitor.models import Service, HealthCheckResult, AIDigest


@pytest.mark.django_db
class TestServiceViewSet:
    """Test cases for Service API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_services(self):
        """Test listing all services."""
        baker.make(Service, _quantity=3)
        
        response = self.client.get('/api/monitor/services/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
    
    def test_create_service(self):
        """Test creating a new service."""
        data = {
            'name': 'New Service',
            'base_url': 'https://api.example.com',
            'health_path': '/health',
            'method': 'GET',
            'headers': {'X-API-Key': 'test'},
            'timeout_s': 5,
            'enabled': True
        }
        
        response = self.client.post('/api/monitor/services/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Service.objects.filter(name='New Service').exists()
    
    def test_update_service(self):
        """Test updating a service."""
        service = baker.make(Service, name='Old Name')
        
        response = self.client.patch(
            f'/api/monitor/services/{service.id}/',
            {'name': 'New Name'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        service.refresh_from_db()
        assert service.name == 'New Name'
    
    def test_delete_service(self):
        """Test deleting a service."""
        service = baker.make(Service)
        
        response = self.client.delete(f'/api/monitor/services/{service.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Service.objects.filter(id=service.id).exists()
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/monitor/services/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestHealthCheckResultViewSet:
    """Test cases for HealthCheckResult API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_results(self):
        """Test listing health check results."""
        service = baker.make(Service)
        baker.make(HealthCheckResult, service=service, _quantity=5)
        
        response = self.client.get('/api/monitor/results/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
    
    def test_filter_by_service(self):
        """Test filtering results by service."""
        service1 = baker.make(Service)
        service2 = baker.make(Service)
        baker.make(HealthCheckResult, service=service1, _quantity=3)
        baker.make(HealthCheckResult, service=service2, _quantity=2)
        
        response = self.client.get(f'/api/monitor/results/?service={service1.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
    
    def test_filter_by_time_range(self):
        """Test filtering results by time range."""
        service = baker.make(Service)
        now = timezone.now()
        
        # Create results at different times
        baker.make(
            HealthCheckResult,
            service=service,
            checked_at=now - timedelta(hours=2)
        )
        baker.make(
            HealthCheckResult,
            service=service,
            checked_at=now - timedelta(hours=1)
        )
        baker.make(
            HealthCheckResult,
            service=service,
            checked_at=now - timedelta(minutes=30)
        )
        
        # Filter last hour
        since = (now - timedelta(hours=1)).isoformat()
        response = self.client.get(f'/api/monitor/results/?since={since}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2


@pytest.mark.django_db
class TestAIDigestViewSet:
    """Test cases for AIDigest API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_digests(self):
        """Test listing AI digests."""
        baker.make(AIDigest, _quantity=3)
        
        response = self.client.get('/api/monitor/digests/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
    
    def test_latest_digest_global(self):
        """Test getting latest global digest."""
        # Create digests with different timestamps
        old_digest = baker.make(
            AIDigest,
            service=None,
            created_at=timezone.now() - timedelta(days=1)
        )
        new_digest = baker.make(
            AIDigest,
            service=None,
            created_at=timezone.now()
        )
        
        response = self.client.get('/api/monitor/digests/latest/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == new_digest.id
        assert response.data['id'] != old_digest.id
    def test_latest_digest_by_service(self):
        """Test getting latest digest for specific service."""
        service = baker.make(Service)
        digest = baker.make(AIDigest, service=service)
        
        response = self.client.get(f'/api/monitor/digests/latest/?service={service.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == digest.id


@pytest.mark.django_db
class TestHealthSummaryView:
    """Test cases for health summary endpoint."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_health_summary(self):
        """Test health summary endpoint."""
        # Create test data
        service = baker.make(Service, name='TestAPI', enabled=True)
        now = timezone.now()
        
        # Create recent health results
        baker.make(
            HealthCheckResult,
            service=service,
            status_code=200,
            ok=True,
            latency_ms=150,
            checked_at=now - timedelta(minutes=5)
        )
        baker.make(
            HealthCheckResult,
            service=service,
            status_code=503,
            ok=False,
            latency_ms=2000,
            checked_at=now - timedelta(hours=2)
        )
        
        # Create AI digest
        digest = baker.make(
            AIDigest,
            service=None,
            summary_text="Test summary",
            anomalies=[{'test': 'anomaly'}]
        )
        
        response = self.client.get('/api/monitor/health/summary/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'services' in response.data
        assert len(response.data['services']) == 1
        
        service_summary = response.data['services'][0]
        assert service_summary['service_name'] == 'TestAPI'
        assert service_summary['latest_check']['status_code'] == 200
        assert service_summary['checks_24h'] == 2
        assert service_summary['errors_24h'] == 1
        assert service_summary['uptime_percentage_24h'] == 50.0
        
        assert response.data['global_digest']['id'] == digest.id