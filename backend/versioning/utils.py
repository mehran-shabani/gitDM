from .models import RecordVersion
import json
from datetime import datetime
from decimal import Decimal

import uuid
from datetime import date
def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def create_version(resource_type, resource_id, data):
    """Create a new version record for a resource"""
    # Get the next version number
    last_version = RecordVersion.objects.filter(
        resource_type=resource_type,
        resource_id=resource_id
    ).order_by('-version_number').first()
    
    version_number = 1 if not last_version else last_version.version_number + 1
    
    # Clean data for JSON serialization
    clean_data = {}
    for key, value in data.items():
        if key.startswith('_'):
            continue  # Skip private attributes
        if value is not None:
            # Convert UUID objects to strings
            if isinstance(value, uuid.UUID):
                clean_data[key] = str(value)
            elif isinstance(value, datetime):
                clean_data[key] = value.isoformat()
            elif isinstance(value, date):
                clean_data[key] = value.isoformat()
            elif isinstance(value, Decimal):
                clean_data[key] = float(value)
            else:
                clean_data[key] = value
    
    # Create version record
    version = RecordVersion.objects.create(
        resource_type=resource_type,
        resource_id=resource_id,
        version_number=version_number,
        data=clean_data
    )
    
    return version