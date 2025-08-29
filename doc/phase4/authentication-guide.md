# Authentication & User Management Guide

## Overview

This application uses JWT (JSON Web Token) authentication for API access with **admin-only user creation**. There is no public user registration or signup functionality.

## User Management

### Creating Users

Users can **only** be created through the Django Admin panel by administrators:

1. Access the admin panel at `/admin/`
2. Login with a superuser account
3. Navigate to "Users" section
4. Create new users with appropriate permissions

**Important**: There are NO public endpoints for user registration. This is by design for security and control.

### User Model

The application uses Django's built-in User model with integer primary keys (not UUIDs). All user-related foreign keys in the system properly reference the User model through Django's ForeignKey fields.

## Authentication Flow

### 1. Obtain JWT Token

Users authenticate by sending their credentials to the token endpoint:

```bash
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Using the Access Token

Include the access token in the Authorization header for all API requests:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 3. Refreshing Tokens

When the access token expires (after 60 minutes), use the refresh token to obtain a new access token:

```bash
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## JWT Configuration

- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 1 day
- **Token Rotation**: Enabled (refresh tokens rotate on use)

## API Security

- All API endpoints require authentication by default
- No public endpoints except for token obtain/refresh
- User creation is restricted to admin panel only
- No UUID-based user creation or management

## System User

The application uses a predefined SYSTEM_USER_ID for system-generated records. This should be configured in your environment settings and should reference a valid user created through the admin panel.

## Best Practices

1. **Admin Access**: Limit admin panel access to trusted administrators only
2. **Strong Passwords**: Enforce strong password policies for all users
3. **Token Security**: Never share or expose JWT tokens
4. **HTTPS Only**: Always use HTTPS in production to protect credentials and tokens
5. **User Auditing**: Monitor user creation and access through Django's admin logs

## Common Scenarios

### Creating API Users for Applications

1. Login to Django admin
2. Create a dedicated user account for the application
3. Assign appropriate permissions
4. Use the credentials to obtain JWT tokens programmatically

### Deactivating Users

1. Access Django admin
2. Find the user account
3. Uncheck "Active" status
4. Save changes

This immediately prevents the user from obtaining new tokens or accessing the API.

## Security Notes

- No public user registration reduces attack surface
- Admin-only user creation ensures controlled access
- JWT tokens provide stateless authentication
- All user references use proper Django ForeignKey relationships (not UUIDs)