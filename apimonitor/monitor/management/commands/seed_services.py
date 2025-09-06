"""
Management command to seed services from JSON file.
"""
import json
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
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
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Confirm destructive actions (required with --clear)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate and show changes without writing to DB'
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Abort all on first invalid item (rollback)'
        )

    def _resolve_file_path(self, file_path: str | None) -> str:
        if file_path:
            # absolute or relative to CWD
            return file_path if os.path.isabs(file_path) else os.path.abspath(file_path)

        # fallback to settings or BASE_DIR/services.json
        default_path = getattr(settings, 'SERVICES_JSON', None)
        if default_path:
            return default_path if os.path.isabs(default_path) else os.path.abspath(default_path)

        # final fallback
        return os.path.join(getattr(settings, 'BASE_DIR', os.getcwd()), 'services.json')

    def _validate_and_normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Validate required fields and coerce defaults/types.
        Raises CommandError on hard errors in strict mode.
        """
        if not isinstance(item, dict):
            raise ValueError('Item must be an object')

        required_fields = ['name', 'base_url']
        missing = [f for f in required_fields if f not in item]
        if missing:
            raise ValueError(f'Missing required fields {missing}')

        method = (item.get('method') or 'GET').upper()
        allowed_methods = {m for (m, _) in Service._meta.get_field('method').choices}
        if method not in allowed_methods:
            # fallback to GET, but warn via return value
            method = 'GET'
            method_warn = True
        else:
            method_warn = False

        headers = item.get('headers', {})
        if headers is None:
            headers = {}
        if not isinstance(headers, dict):
            raise ValueError('headers must be a JSON object')

        timeout_s = item.get('timeout_s', 5)
        try:
            timeout_s = int(timeout_s)
        except (ValueError, TypeError):
            raise ValueError('timeout_s must be an integer (seconds)')
        if timeout_s <= 0:
            raise ValueError('timeout_s must be > 0')

        normalized = {
            'name': item['name'],
            'base_url': item['base_url'],
            'health_path': item.get('health_path', '/health'),
            'method': method,
            'headers': headers,
            'timeout_s': timeout_s,
            'enabled': bool(item.get('enabled', True)),
        }
        return normalized | {'_method_warn': method_warn}

    def handle(self, *args: object, **options: Any) -> None:
        file_path = self._resolve_file_path(options.get('file'))

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

        clear = bool(options.get('clear'))
        confirm = bool(options.get('yes'))
        dry_run = bool(options.get('dry_run'))
        strict = bool(options.get('strict'))

        if clear and not confirm:
            raise CommandError('Use --yes together with --clear to confirm deletion of existing services.')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Wrap entire run in a transaction (rollback on exception)
        with transaction.atomic():
            # Clear existing services if requested
            if clear:
                if dry_run:
                    count = Service.objects.count()
                    self.stdout.write(self.style.WARNING(f'[dry-run] Would delete {count} existing services'))
                else:
                    deleted = Service.objects.all().delete()
                    self.stdout.write(self.style.WARNING(f'Deleted {deleted[0]} existing services'))

            for raw in services_data:
                try:
                    normalized = self._validate_and_normalize(raw)
                except ValueError as e:
                    skipped_count += 1
                    msg = f'Skipping invalid service item: {e}; payload={raw!r}'
                    if strict:
                        # abort everything
                        raise CommandError(msg)
                    self.stdout.write(self.style.ERROR(msg))
                    continue

                name = normalized.pop('name')
                method_warn = normalized.pop('_method_warn', False)

                # Pre-validate model constraints
                candidate = Service(name=name, **normalized)
                try:
                    candidate.full_clean()
                except Exception as e:
                    skipped_count += 1
                    msg = f'Skipping invalid service "{name}": {e}'
                    if strict:
                        raise CommandError(msg)
                    self.stdout.write(self.style.ERROR(msg))
                    continue

                if dry_run:
                    # Determine create/update by existence
                    exists = Service.objects.filter(name=name).only('id').exists()
                    if exists:
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'[dry-run] Would update service: {name}'))
                    else:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'[dry-run] Would create service: {name}'))
                    if method_warn:
                        self.stdout.write(self.style.WARNING(f'[dry-run] Method invalid for "{name}", falling back to GET'))
                    continue

                service, created = Service.objects.update_or_create(
                    name=name,
                    defaults=normalized
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Updated service: {service.name}'))
                if method_warn:
                    self.stdout.write(self.style.WARNING(
                        f'Invalid method for "{name}", fell back to GET'
                    ))

            if dry_run:
                # Ensure no DB changes persist
                transaction.set_rollback(True)

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count}, Updated {updated_count}, Skipped {skipped_count}'
            )
        )
