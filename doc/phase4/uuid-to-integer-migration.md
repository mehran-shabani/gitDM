# UUID to Integer ID Migration Guide

## Overview

This project has been migrated from using UUID primary keys to using Django's default integer AutoField primary keys. This change was made to:
- Simplify the codebase
- Improve compatibility with Django's default User model
- Reduce complexity in serialization and API interactions
- Improve database performance

## Changes Made

### 1. Model Changes
All models now use `models.AutoField(primary_key=True)` instead of `models.UUIDField`:
- `Patient`
- `Encounter`
- `LabResult`
- `MedicationOrder`
- `ClinicalReference`
- `AISummary`

### 2. Generic Foreign Key Updates
- `AISummary.object_id`: Changed from `UUIDField` to `PositiveIntegerField`
- `RecordVersion.resource_id`: Changed from `UUIDField` to `PositiveIntegerField`

### 3. Configuration Changes
- `SYSTEM_USER_ID` in settings.py: Changed from UUID string to integer (1)

### 4. Serializer Updates
- `PatientSerializer.primary_doctor_id`: Changed from `UUIDField` to `IntegerField`

### 5. View Updates
- Removed UUID imports and conversions
- `SYSTEM_USER_ID` now uses integer value

### 6. Test Updates
- Removed UUID imports
- Updated test payloads to use integer IDs
- Changed non-existent ID references from `uuid.uuid4()` to large integers like `999999`

## Migration Steps

### For New Installations

1. Create fresh migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Create the system user (ID=1) through Django admin

### For Existing Installations

**WARNING**: This is a breaking change. Existing data with UUID primary keys will need to be migrated manually.

1. Backup your database
2. Export existing data (if needed)
3. Drop all tables
4. Run fresh migrations
5. Re-import data with new integer IDs

## API Changes

### Before (UUID-based)
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "primary_doctor_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### After (Integer-based)
```json
{
    "id": 1,
    "primary_doctor_id": 2
}
```

## Testing

All tests have been updated to use integer IDs. Run tests with:
```bash
pytest
```

## Notes

- The Django User model uses integer primary keys by default
- All foreign key relationships now properly reference integer IDs
- No UUID imports or dependencies remain in the codebase