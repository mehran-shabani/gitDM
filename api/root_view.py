from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API Root - Diabetes Management System
    
    This API requires JWT authentication for all endpoints except token endpoints.
    Users must be created through the Django admin panel - there is no public user registration.
    """
    return Response({
        'message': 'Diabetes Management System API',
        'authentication': {
            'type': 'JWT (JSON Web Token)',
            'obtain_token': request.build_absolute_uri('/api/token/'),
            'refresh_token': request.build_absolute_uri('/api/token/refresh/'),
            'header_format': 'Authorization: Bearer <token>',
        },
        'user_management': {
            'registration': 'Admin panel only - no public registration',
            'admin_url': request.build_absolute_uri('/admin/'),
            'note': 'Contact system administrator for user account creation',
        },
        'endpoints': {
            'patients': request.build_absolute_uri('/api/patients/'),
            'encounters': request.build_absolute_uri('/api/encounters/'),
            'labs': request.build_absolute_uri('/api/labs/'),
            'medications': request.build_absolute_uri('/api/meds/'),
            'references': request.build_absolute_uri('/api/refs/'),
        },
        'documentation': {
            'schema': request.build_absolute_uri('/api/schema/'),
            'swagger': request.build_absolute_uri('/api/docs/'),
        }
    })