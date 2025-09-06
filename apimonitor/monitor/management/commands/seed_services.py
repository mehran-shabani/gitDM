"""
Management command to seed services from JSON file.
"""
import json
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from monitor.models import Service


class Command(BaseCommand):
    help = 'Seed services from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Path to JSON file containing services'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing services before seeding'
        )

    def handle(self, *args: object, **options: Any) -> None:
        # Determine file path
        file_path = options.get('file')
        if not file_path:
            # Try to get from settings
            file_path = getattr(settings, 'SERVICES_JSON', './services.json')
        
        if not os.path.exists(file_path):
            raise CommandError(f'Services file not found: {file_path}')
        
        # Load services from JSON
        try:
            with open(file_path, encoding='utf-8') as f:
                services_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON in {file_path}: {e}') from e
        except OSError as e:
            raise CommandError(f'Error reading {file_path}: {e}') from e
        
        if not isinstance(services_data, list):
            raise CommandError('Services JSON must be an array of service objects')
        
        # Clear existing services if requested
        if options.get('clear'):
            deleted = Service.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted[0]} existing services')
            )
        
        # Create or update services
        created_count = 0
        updated_count = 0
        
        for service_data in services_data:
            # Validate required fields
            required_fields = ['name', 'base_url']
            missing = [f for f in required_fields if f not in service_data]
            if missing:
                self.stdout.write(
                    self.style.ERROR(
                        f'Skipping service missing required fields {missing}: {service_data}'
                    )
                )
                continue
            
            # Extract fields with defaults
            defaults = {
                'base_url': service_data['base_url'],
                'health_path': service_data.get('health_path', '/health'),
                'method': service_data.get('method', 'GET').upper(),
                'headers': service_data.get('headers', {}),
                'timeout_s': service_data.get('timeout_s', 5),
                'enabled': service_data.get('enabled', True),
            }
            
            # Create or update service
            service, created = Service.objects.update_or_create(
                name=service_data['name'],
                defaults=defaults
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated service: {service.name}')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} services, '
                f'updated {updated_count} services'
            )
        )
