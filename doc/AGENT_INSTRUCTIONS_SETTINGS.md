# Important Instructions for Agents: Django Settings Configuration

## ⚠️ CRITICAL: DO NOT MODIFY SETTINGS ⚠️

### Overview
The Django settings configuration has already been properly set up with security improvements and proper environment variable handling. These settings MUST NOT be changed or committed further.

### Current Settings Status
The following security and configuration improvements have already been implemented in `config/settings.py`:

1. **SECRET_KEY Security** ✅
   - Production requires `DJANGO_SECRET_KEY` environment variable
   - Development mode uses a safe default only when `DEBUG=True`
   - Raises `ImproperlyConfigured` exception if missing in production

2. **ALLOWED_HOSTS Security** ✅
   - Production requires `DJANGO_ALLOWED_HOSTS` environment variable
   - Development mode defaults to `['localhost', '127.0.0.1', '[::1]']`
   - Raises `ImproperlyConfigured` exception if missing in production

3. **Test Configuration** ✅
   - `pytest.ini` correctly uses `config.test_settings`
   - Tests run against SQLite in-memory database, not production

### Instructions for Agents

When working on this project, follow these guidelines:

1. **DO NOT MODIFY** any of the following files related to settings:
   - `config/settings.py`
   - `config/test_settings.py`
   - `pytest.ini`
   - `.env.example`

2. **DO NOT COMMIT** any changes to settings files even if you need to make temporary local changes

3. **USE ENVIRONMENT VARIABLES** for any configuration needs:
   - Copy `.env.example` to `.env` for local development
   - Never commit `.env` files
   - Use the existing environment variable structure

4. **FOR LOCAL DEVELOPMENT**:
   - Refer to `doc/local-development-without-containers.md` for setup instructions
   - Use the documented environment variables
   - Create `config/local_settings.py` if you need custom local overrides (never commit this file)

5. **IF SETTINGS CHANGES ARE NEEDED**:
   - Document the requirement but DO NOT implement
   - Explain why the change is needed
   - Let the project maintainer handle settings modifications

### Example Agent Prompt

When instructing another agent, use this template:

```
IMPORTANT: The Django settings configuration has been finalized and secured. 

DO NOT:
- Modify config/settings.py or any settings-related files
- Change SECRET_KEY or ALLOWED_HOSTS configuration
- Alter pytest.ini configuration
- Commit any settings changes

REFER TO:
- doc/local-development-without-containers.md for local setup
- .env.example for environment variable configuration

The settings have been secured with proper production safeguards and must remain unchanged.
```

### Security Fixes Already Applied

For reference, these security issues have been resolved:
- Critical: SECRET_KEY no longer has unsafe defaults in production
- High: ALLOWED_HOSTS restricted properly
- High: Test configuration uses separate test database
- All models updated to use proper Django patterns (ForeignKey, GenericForeignKey, DecimalField)

### Summary

The settings are production-ready and secure. Any agent working on this project should:
1. Use the existing configuration as-is
2. Configure their environment using `.env` files
3. Never modify or commit changes to core settings files
4. Refer to existing documentation for setup instructions

**Remember: Settings are frozen. Use them, don't change them.**