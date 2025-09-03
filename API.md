# GitDM API Documentation

This document provides comprehensive documentation for all GitDM API endpoints, including request/response formats, authentication requirements, and usage examples.

## 🔐 Authentication

GitDM uses JWT (JSON Web Token) authentication for API access.

### Obtaining Tokens

**Endpoint**: `POST /api/token/`

**Request Body**:
```json
{
    "email": "doctor@example.com",
    "password": "your_password"
}
```

**Response**:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refreshing Tokens

**Endpoint**: `POST /api/token/refresh/`

**Request Body**:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Tokens

Include the access token in the Authorization header for all protected endpoints:

```bash
Authorization: Bearer <ACCESS_TOKEN>
```

## 👥 Patient Management

### List Patients

**Endpoint**: `GET /api/patients/`

**Description**: Retrieve list of patients accessible to the authenticated doctor

**Query Parameters**:
- `limit` (optional): Number of results per page
- `offset` (optional): Pagination offset

**Response**:
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/patients/?limit=20&offset=20",
    "previous": null,
    "results": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "full_name": "احمد محمدی",
            "national_id": "1234567890",
            "age": 45,
            "diabetes_type": "TYPE2",
            "primary_doctor": "doctor@example.com",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Create Patient

**Endpoint**: `POST /api/patients/`

**Request Body**:
```json
{
    "full_name": "علی احمدی",
    "national_id": "9876543210",
    "age": 52,
    "diabetes_type": "TYPE2",
    "phone": "+989123456789",
    "emergency_contact": "+989987654321"
}
```

**Response**: `201 Created` with patient object

### Get Patient Details

**Endpoint**: `GET /api/patients/{id}/`

**Response**: Complete patient object with all fields

### Update Patient

**Endpoint**: `PUT /api/patients/{id}/` or `PATCH /api/patients/{id}/`

**Request Body**: Patient fields to update

### Delete Patient

**Endpoint**: `DELETE /api/patients/{id}/`

**Response**: `204 No Content`

### Patient Timeline

**Endpoint**: `GET /api/patients/{id}/timeline/`

**Description**: Retrieve comprehensive timeline of all patient interactions

**Query Parameters**:
- `limit` (optional): Maximum 500 entries, default 100

**Response**:
```json
{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "timeline": [
        {
            "date": "2024-01-15T10:30:00Z",
            "type": "encounter",
            "title": "ویزیت معمول",
            "description": "بررسی کنترل قند خون",
            "severity": "normal",
            "data": {
                "blood_pressure": "120/80",
                "weight": "75kg"
            }
        },
        {
            "date": "2024-01-10T09:15:00Z",
            "type": "lab_result",
            "title": "آزمایش HbA1c",
            "description": "نتیجه: 7.2%",
            "severity": "warning",
            "data": {
                "value": 7.2,
                "unit": "%",
                "reference_range": "< 7.0%"
            }
        }
    ]
}
```

## 🏥 Clinical Encounters

### List Encounters

**Endpoint**: `GET /api/encounters/`

**Query Parameters**:
- `patient` (optional): Filter by patient ID
- `date_from` (optional): Start date filter (YYYY-MM-DD)
- `date_to` (optional): End date filter (YYYY-MM-DD)

### Create Encounter

**Endpoint**: `POST /api/encounters/`

**Request Body**:
```json
{
    "patient": "123e4567-e89b-12d3-a456-426614174000",
    "encounter_date": "2024-01-15",
    "subjective": "بیمار احساس خستگی می‌کند",
    "objective": "فشار خون: 130/85، وزن: 75 کیلوگرم",
    "assessment": "کنترل نسبی دیابت",
    "plan": "ادامه متفورمین، کنترل قند در 2 هفته"
}
```

### Get/Update/Delete Encounter

- `GET /api/encounters/{id}/`
- `PUT/PATCH /api/encounters/{id}/`
- `DELETE /api/encounters/{id}/`

## 🔬 Laboratory Results

### List Lab Results

**Endpoint**: `GET /api/labs/`

**Query Parameters**:
- `patient` (optional): Filter by patient ID
- `test_type` (optional): Filter by test type
- `date_from` (optional): Start date filter

### Create Lab Result

**Endpoint**: `POST /api/labs/`

**Request Body**:
```json
{
    "patient": "123e4567-e89b-12d3-a456-426614174000",
    "test_name": "HbA1c",
    "loinc_code": "4548-4",
    "value": 7.2,
    "unit": "%",
    "reference_range": "< 7.0%",
    "test_date": "2024-01-15"
}
```

## 💊 Medication Management

### List Medications

**Endpoint**: `GET /api/meds/`

**Query Parameters**:
- `patient` (optional): Filter by patient ID
- `active` (optional): Filter active medications (true/false)

### Create Medication Order

**Endpoint**: `POST /api/meds/`

**Request Body**:
```json
{
    "patient": "123e4567-e89b-12d3-a456-426614174000",
    "medication_name": "متفورمین",
    "atc_code": "A10BA02",
    "dosage": "500mg",
    "frequency": "دو بار در روز",
    "duration": "30 روز",
    "instructions": "با غذا مصرف شود"
}
```

## 📚 Clinical References

### List References

**Endpoint**: `GET /api/refs/`

**Query Parameters**:
- `category` (optional): Filter by reference category
- `search` (optional): Search in title and content

### Create Reference

**Endpoint**: `POST /api/refs/`

**Request Body**:
```json
{
    "title": "راهنمای کنترل دیابت نوع 2",
    "category": "diabetes_management",
    "content": "محتوای راهنمای بالینی...",
    "source": "انجمن دیابت ایران",
    "url": "https://example.com/guideline"
}
```

## 🤖 AI Summaries

### List AI Summaries

**Endpoint**: `GET /api/ai-summaries/`

**Query Parameters**:
- `patient_id` (optional): Filter by patient ID

**Response**:
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "patient": "123e4567-e89b-12d3-a456-426614174000",
            "summary": "خلاصه وضعیت بیمار...",
            "resource_type": "encounter",
            "references": [1, 2],
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Create AI Summary

**Endpoint**: `POST /api/ai-summaries/`

**Request Body**:
```json
{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "content_type": "encounter",
    "object_id": "456",
    "prompt_template": "custom" // optional
}
```

### Additional AI Endpoints

- `POST /api/ai-summaries/{id}/regenerate/` - Regenerate existing summary
- `POST /api/ai-summaries/test/` - Test AI service connection
- `GET /api/ai-summaries/stats/` - Summary statistics
- `POST /api/ai-summaries/test-references/` - Test reference linking

## 📊 Analytics & Pattern Analysis

### Baseline Metrics

**Endpoint**: `GET /api/baseline-metrics/`

**Description**: Patient baseline metrics for anomaly detection

**Query Parameters**:
- `patient_id` (optional): Filter by patient

**Response**:
```json
{
    "results": [
        {
            "patient": "123e4567-e89b-12d3-a456-426614174000",
            "avg_hba1c": "7.20",
            "avg_blood_glucose": "145.50",
            "std_hba1c": "0.80",
            "std_blood_glucose": "25.30",
            "last_calculated": "2024-01-15T10:30:00Z"
        }
    ]
}
```

**Calculate Baseline**: `POST /api/baseline-metrics/calculate/`

### Pattern Analysis

**Endpoint**: `GET /api/pattern-analyses/`

**Description**: List pattern analysis results

**Request Analysis**: `POST /api/pattern-analyses/analyze/`

**Request Body**:
```json
{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "analysis_type": "glucose_trend",
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-01-31"
    }
}
```

### Anomaly Detection

**Endpoint**: `GET /api/anomaly-detections/`

**Description**: List detected anomalies requiring attention

**Response**:
```json
{
    "results": [
        {
            "id": 1,
            "patient": "123e4567-e89b-12d3-a456-426614174000",
            "anomaly_type": "glucose_spike",
            "severity": "high",
            "description": "افزایش ناگهانی قند خون",
            "detected_at": "2024-01-15T10:30:00Z",
            "acknowledged": false
        }
    ]
}
```

**Acknowledge Anomaly**: `POST /api/anomaly-detections/{id}/acknowledge/`

### Pattern Alerts

**Endpoint**: `GET /api/pattern-alerts/`

**Description**: List active pattern-based alerts

**Resolve Alert**: `POST /api/pattern-alerts/{id}/resolve/`

## 🔔 Notifications & Reminders

### Notifications

**Endpoint**: `GET /api/notifications/`

**Description**: List user notifications

**Response**:
```json
{
    "results": [
        {
            "id": 1,
            "title": "یادآوری آزمایش",
            "message": "زمان انجام آزمایش HbA1c فرا رسیده",
            "type": "lab_reminder",
            "priority": "high",
            "read": false,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Clinical Alerts

**Endpoint**: `GET /api/alerts/`

**Description**: List clinical alerts requiring immediate attention

### Reminders

**Endpoint**: `GET /api/reminders/`

**Description**: List active reminders for patients

**Query Parameters**:
- `patient_id` (optional): Filter by patient
- `reminder_type` (optional): Filter by type (medication, lab_test, appointment)
- `status` (optional): Filter by status (pending, completed, overdue)

## 📈 Analytics Endpoints

### Patient Analytics

**Endpoint**: `GET /api/analytics/patient-analytics/`

**Description**: Comprehensive patient analytics data

**Calculate Analytics**: `POST /api/analytics/patient-analytics/calculate/`

**Request Body**:
```json
{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-01-31"
    }
}
```

### Doctor Performance

**Endpoint**: `GET /api/analytics/doctor-performance/`

**Description**: Doctor performance metrics and statistics

### System Analytics

**Endpoint**: `GET /api/analytics/system-overview/`

**Description**: System-wide analytics and usage statistics

### Reports

**Generate Patient Report**: `POST /api/analytics/reports/patient/`

**Request Body**:
```json
{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "report_type": "comprehensive", // or "summary", "lab_only"
    "format": "pdf", // or "excel", "csv"
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-01-31"
    }
}
```

**Generate Doctor Report**: `POST /api/analytics/reports/doctor/`

**Generate System Report**: `POST /api/analytics/reports/system/`

## 🔄 Versioning System

### List Versions

**Endpoint**: `GET /api/versions/{resource_type}/{resource_id}/`

**Parameters**:
- `resource_type`: Type of resource (patient, encounter, lab, medication, etc.)
- `resource_id`: ID of the specific resource

**Response**:
```json
[
    {
        "version": 3,
        "timestamp": "2024-01-15T10:30:00Z",
        "user": "doctor@example.com",
        "changes": {
            "field": "medication_dosage",
            "old_value": "500mg",
            "new_value": "1000mg"
        }
    }
]
```

### Revert to Version

**Endpoint**: `POST /api/versions/{resource_type}/{resource_id}/revert/`

**Request Body**:
```json
{
    "target_version": 2
}
```

## 📤 Data Export

### Export Patient Data

**Endpoint**: `GET /api/export/patient/{patient_id}/`

**Description**: Export comprehensive patient data including all encounters, lab results, medications, and AI summaries

**Response**: JSON object with complete patient data structure

```json
{
    "patient": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "احمد محمدی",
        "national_id": "1234567890"
    },
    "encounters": [...],
    "lab_results": [...],
    "medications": [...],
    "ai_summaries": [...]
}
```

## 🏥 System Health & Monitoring

### Health Check

**Endpoint**: `GET /health/`

**Description**: Basic system health check

**Response**:
```json
{
    "status": "ok"
}
```

### API Root

**Endpoint**: `GET /api/`

**Description**: API root status endpoint

**Response**:
```json
{
    "status": "ok"
}
```

## 📋 Request/Response Formats

### Standard Response Format

All API responses follow a consistent format:

**Success Response**:
```json
{
    "count": 10,
    "next": "http://localhost:8000/api/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```

**Error Response**:
```json
{
    "error": "Invalid request",
    "detail": "Detailed error message",
    "code": "VALIDATION_ERROR"
}
```

### Common HTTP Status Codes

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## 🔍 Query Parameters

### Common Parameters

- `limit`: Number of results per page (default: 20, max: 100)
- `offset`: Pagination offset
- `ordering`: Sort field (prefix with `-` for descending)
- `search`: Text search in relevant fields

### Date Filtering

Many endpoints support date filtering:
- `date_from`: Start date (YYYY-MM-DD format)
- `date_to`: End date (YYYY-MM-DD format)
- `created_after`: Filter by creation date
- `updated_after`: Filter by update date

## 🎯 Advanced Features

### Bulk Operations

Some endpoints support bulk operations for efficiency:

**Bulk Create Lab Results**: `POST /api/labs/bulk/`

**Request Body**:
```json
{
    "results": [
        {
            "patient": "123e4567-e89b-12d3-a456-426614174000",
            "test_name": "FBS",
            "value": 120,
            "unit": "mg/dL"
        },
        {
            "patient": "123e4567-e89b-12d3-a456-426614174000",
            "test_name": "HbA1c",
            "value": 7.1,
            "unit": "%"
        }
    ]
}
```

### Filtering and Search

Advanced filtering is available on most list endpoints:

**Example**: `GET /api/patients/?diabetes_type=TYPE2&age__gte=40&search=احمد`

### Field Selection

Use `fields` parameter to select specific fields:

**Example**: `GET /api/patients/?fields=id,full_name,diabetes_type`

## 🔧 Error Handling

### Validation Errors

**Response** (400 Bad Request):
```json
{
    "field_name": [
        "This field is required."
    ],
    "non_field_errors": [
        "General validation error message."
    ]
}
```

### Authentication Errors

**Response** (401 Unauthorized):
```json
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": "access",
            "message": "Token is invalid or expired"
        }
    ]
}
```

### Permission Errors

**Response** (403 Forbidden):
```json
{
    "detail": "You do not have permission to perform this action."
}
```

## 🚀 Rate Limiting

API requests are subject to rate limiting:
- **Authenticated users**: 1000 requests per hour
- **AI endpoints**: 100 requests per hour
- **Export endpoints**: 10 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642781234
```

## 📱 API Clients

### cURL Examples

**Authentication**:
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email": "doctor@example.com", "password": "password"}'
```

**Create Patient**:
```bash
curl -X POST http://localhost:8000/api/patients/ \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"full_name": "علی احمدی", "diabetes_type": "TYPE2"}'
```

**Get Patient Timeline**:
```bash
curl -H 'Authorization: Bearer <TOKEN>' \
  http://localhost:8000/api/patients/<PATIENT_ID>/timeline/?limit=50
```

### Python Client Example

```python
import requests

# Authenticate
auth_response = requests.post('http://localhost:8000/api/token/', {
    'email': 'doctor@example.com',
    'password': 'password'
})
token = auth_response.json()['access']

# Set headers
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Create patient
patient_data = {
    'full_name': 'علی احمدی',
    'diabetes_type': 'TYPE2',
    'age': 45
}
response = requests.post('http://localhost:8000/api/patients/', 
                        json=patient_data, headers=headers)
patient = response.json()

# Get patient timeline
timeline_response = requests.get(
    f'http://localhost:8000/api/patients/{patient["id"]}/timeline/',
    headers=headers
)
timeline = timeline_response.json()
```

## 🔗 Interactive Documentation

For interactive API exploration, visit:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

These interfaces provide real-time API testing capabilities and comprehensive schema documentation.

---

*This documentation is automatically generated from the OpenAPI specification. For the most up-to-date API details, refer to the interactive documentation interfaces.*