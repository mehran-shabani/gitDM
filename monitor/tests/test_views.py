"""Tests for DRF views."""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from model_bakery import baker

from gitdm.models import User
from monitor.models import Service, HealthCheckResult, AIDigest


@pytest.mark.django_db
class TestServiceViewSet:
    """Test Service CRUD operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = baker.make(User, is_staff=True)
        self.client.force_authenticate(user=self.user)
    
    def test_list_services(self):
        """Test listing services."""
        baker.make(Service, _quantity=3)
        
        url = reverse('monitor:service-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 3
        else:
            assert len(response.data) == 3
    
    def test_create_service(self):
        """Test creating a new service."""
        url = reverse('monitor:service-list')
        data = {
            'name': 'NewAPI',
            'base_url': 'https://new-api.com',
            'health_path': '/health',
            'method': 'GET',
            'headers': {'X-API-Key': 'test'},
            'timeout_s': 5,
            'enabled': True
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Service.objects.filter(name='NewAPI').exists()
    
    def test_update_service(self):
        """Test updating a service."""
        service = baker.make(Service, name='OldName')
        
        url = reverse('monitor:service-detail', kwargs={'pk': service.pk})
        data = {'name': 'NewName'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        service.refresh_from_db()
        assert service.name == 'NewName'
    
    def test_delete_service(self):
        """Test deleting a service."""
        service = baker.make(Service)
        
        url = reverse('monitor:service-detail', kwargs={'pk': service.pk})
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Service.objects.filter(pk=service.pk).exists()


@pytest.mark.django_db
class TestHealthCheckResultViewSet:
    """Test HealthCheckResult views."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = baker.make(User, is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.service = baker.make(Service, name='TestAPI')
    
    def test_list_health_results(self):
        """Test listing health check results."""
        baker.make(HealthCheckResult, service=self.service, _quantity=5)
        
        url = reverse('monitor:healthcheckresult-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 5
        else:
            assert len(response.data) == 5
    
    def test_filter_by_service(self):
        """Test filtering results by service."""
        other_service = baker.make(Service, name='OtherAPI')
        
        baker.make(HealthCheckResult, service=self.service, _quantity=3)
        baker.make(HealthCheckResult, service=other_service, _quantity=2)
        
        url = reverse('monitor:healthcheckresult-list')
        response = self.client.get(url, {'service': self.service.pk})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 3
        else:
            assert len(response.data) == 3
    
    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        now = timezone.now()
        old_time = now - timezone.timedelta(days=2)
        recent_time = now - timezone.timedelta(hours=1)
        
        # Old result
        baker.make(HealthCheckResult, service=self.service, checked_at=old_time)
        # Recent result
        baker.make(HealthCheckResult, service=self.service, checked_at=recent_time)
        
        url = reverse('monitor:healthcheckresult-list')
        
        # Filter since yesterday
        since = (now - timezone.timedelta(days=1)).isoformat()
        response = self.client.get(url, {'since': since})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 1  # Only recent result
        else:
            assert len(response.data) == 1
    
    def test_filter_by_status(self):
        """Test filtering by ok status."""
        baker.make(HealthCheckResult, service=self.service, ok=True, _quantity=3)
        baker.make(HealthCheckResult, service=self.service, ok=False, _quantity=2)
        
        url = reverse('monitor:healthcheckresult-list')
        response = self.client.get(url, {'ok': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 3
        else:
            assert len(response.data) == 3


@pytest.mark.django_db
class TestAIDigestViewSet:
    """Test AIDigest views."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = baker.make(User, is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.service = baker.make(Service, name='TestAPI')
    
    def test_list_digests(self):
        """Test listing AI digests."""
        baker.make(AIDigest, service=self.service, _quantity=3)
        
        url = reverse('monitor:aidigest-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            assert len(response.data['results']) == 3
        else:
            assert len(response.data) == 3
    
    def test_latest_digest_endpoint(self):
        """Test latest digest endpoint."""
        # Create digests with different timestamps
        old_digest = baker.make(
            AIDigest, 
            service=self.service,
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        latest_digest = baker.make(
            AIDigest, 
            service=self.service,
            created_at=timezone.now()
        )
        
        url = reverse('monitor:aidigest-latest')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == latest_digest.id
    
    def test_latest_digest_filtered_by_service(self):
        """Test latest digest filtered by service."""
        other_service = baker.make(Service, name='OtherAPI')
        
        baker.make(AIDigest, service=other_service)
        target_digest = baker.make(AIDigest, service=self.service)
        
        url = reverse('monitor:aidigest-latest')
        response = self.client.get(url, {'service': self.service.pk})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == target_digest.id
    
    def test_latest_digest_not_found(self):
        """Test latest digest when none exists."""
        url = reverse('monitor:aidigest-latest')
        response = self.client.get(url, {'service': 999})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestHealthSummaryView:
    """Test health summary endpoint."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = baker.make(User, is_staff=True)
        self.client.force_authenticate(user=self.user)
    
    def test_health_summary_empty(self):
        """Test health summary with no services."""
        url = reverse('monitor:health-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['services'] == []
        assert response.data['global_digest'] is None
    
    def test_health_summary_with_data(self):
        """Test health summary with services and data."""
        # Create services
        service1 = baker.make(Service, name='API1', enabled=True)
        service2 = baker.make(Service, name='API2', enabled=True)
        
        # Create health check results
        result1 = baker.make(HealthCheckResult, service=service1, ok=True)
        result2 = baker.make(HealthCheckResult, service=service2, ok=False)
        
        # Create AI digests
        digest1 = baker.make(AIDigest, service=service1)
        global_digest = baker.make(AIDigest, service=None)
        
        url = reverse('monitor:health-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['services']) == 2
        
        # Check service data structure
        service_data = response.data['services'][0]
        assert 'service_id' in service_data
        assert 'service_name' in service_data
        assert 'latest_check' in service_data
        assert 'latest_digest' in service_data
        
        # Check global digest
        assert response.data['global_digest'] is not None
        assert response.data['global_digest']['id'] == global_digest.id
    
    def test_health_summary_unauthenticated(self):
        """Test health summary requires authentication."""
        client = APIClient()  # No authentication
        url = reverse('monitor:health-summary')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED