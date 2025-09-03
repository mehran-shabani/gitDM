"""Management command to seed services from JSON file."""

import json
import os
from pathlib import Path
from typing import Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from monitor.models import Service


class Command(BaseCommand):
    """Seed services from JSON configuration file."""
    
    help = 'Load services from JSON file into the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Path to JSON file containing services (default: from SERVICES_JSON env var)'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing services instead of skipping them'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing services before loading new ones'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        
        # Determine JSON file path
        json_file = options.get('file')
        if not json_file:
            json_file = os.getenv('SERVICES_JSON', './services.json')
        
        json_path = Path(json_file)
        if not json_path.is_absolute():
            json_path = Path(settings.BASE_DIR) / json_path
        
        if not json_path.exists():
            raise CommandError(f"JSON file not found: {json_path}")
        
        # Load JSON data
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")
        
        if not isinstance(services_data, list):
            raise CommandError("JSON file must contain an array of service objects")
        
        # Clear existing services if requested
        if options['clear']:
            deleted_count = Service.objects.count()
            Service.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {deleted_count} existing services")
            )
        
        # Process each service
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for service_data in services_data:
            try:
                result = self._create_or_update_service(service_data, options['update'])
                
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing service {service_data.get('name', 'unknown')}: {e}")
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nServices processed successfully!\n"
                f"Created: {created_count}\n"
                f"Updated: {updated_count}\n"
                f"Skipped: {skipped_count}"
            )
        )
    
    def _create_or_update_service(self, service_data: Dict[str, Any], update_existing: bool) -> str:
        """Create or update a single service."""
        
        # Validate required fields
        required_fields = ['name', 'base_url']
        for field in required_fields:
            if field not in service_data:
                raise ValueError(f"Missing required field: {field}")
        
        name = service_data['name']
        
        # Check if service exists
        service_exists = False
        try:
            service = Service.objects.get(name=name)
            service_exists = True
            if not update_existing:
                self.stdout.write(f"Service '{name}' already exists, skipping...")
                return 'skipped'
        except Service.DoesNotExist:
            service = Service(name=name)
        
        # Update service fields
        service.base_url = service_data['base_url']
        service.health_path = service_data.get('health_path', '/health')
        service.method = service_data.get('method', 'GET')
        service.headers = service_data.get('headers', {})
        service.timeout_s = service_data.get('timeout_s', 5)
        service.enabled = service_data.get('enabled', True)
        
        # Validate method
        if service.method not in ['GET', 'POST', 'HEAD']:
            raise ValueError(f"Invalid method '{service.method}' for service '{name}'")
        
        # Validate timeout
        if not isinstance(service.timeout_s, int) or service.timeout_s < 1 or service.timeout_s > 300:
            raise ValueError(f"Invalid timeout '{service.timeout_s}' for service '{name}'")
        
        # Validate headers
        if not isinstance(service.headers, dict):
            raise ValueError(f"Headers must be a dictionary for service '{name}'")
        
        service.save()
        
        action = 'updated' if service_exists else 'created'
        self.stdout.write(f"Service '{name}' {action} successfully")
        
        return action