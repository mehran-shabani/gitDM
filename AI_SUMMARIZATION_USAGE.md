# AI Summarization with GapGPT Integration

This Django application now supports AI-powered medical data summarization using GapGPT API (with OpenAI fallback).

## Setup

### 1. Install Dependencies

The required packages are already included in `requirements.txt`:

- `openai>=1.65.0`
- Other dependencies...

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Primary AI Service (GapGPT)
GAPGPT_API_KEY=your-gapgpt-api-key-here
GAPGPT_BASE_URL=https://api.gapgpt.app/v1
USE_GAPGPT=True

# Fallback AI Service (OpenAI)
OPENAI_API_KEY=your-openai-api-key-here

# AI Model Configuration
AI_MODEL=gpt-4o
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.3
```

### 3. Run Migrations

```bash
python manage.py migrate
```

## API Endpoints

### Base URL: `/api/ai-summaries/`

#### 1. Create AI Summary

**POST** `/api/ai-summaries/`

```json
{
    "patient_id": 1,
    "content": "Patient presents with elevated blood glucose levels. HbA1c is 8.2%. Started on metformin 500mg twice daily.",
    "context": "Patient is a 45-year-old male with newly diagnosed Type 2 diabetes",
    "summary_type": "encounter",
    "topic_hint": "diabetes",
    "async_processing": true
}
```

**Response (Async):**

```json
{
    "task_id": "uuid-here",
    "status": "processing",
    "message": "AI summary is being generated in the background"
}
```

**Response (Sync - when async_processing=false):**

```json
{
    "id": "uuid-here",
    "patient": 1,
    "summary": "Patient presents with poorly controlled Type 2 diabetes with HbA1c of 8.2%...",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
}
```

#### 2. List AI Summaries

**GET** `/api/ai-summaries/?patient_id=1`

#### 3. Get AI Summary

**GET** `/api/ai-summaries/{id}/`

#### 4. Regenerate AI Summary

**POST** `/api/ai-summaries/{id}/regenerate/`

```json
{
    "content": "Updated medical information...",
    "context": "Additional context...",
    "summary_type": "medical_record"
}
```

#### 5. Test AI Service

**POST** `/api/ai-summaries/test/`

```json
{
    "content": "Test patient data for AI processing"
}
```

#### 6. Get Statistics

**GET** `/api/ai-summaries/stats/?patient_id=1`

#### 7. Test Clinical References Linking

**POST** `/api/ai-summaries/test-references/`

```json
{
    "content": "Patient has diabetes with elevated HbA1c. Starting metformin and insulin therapy.",
    "topic_hint": "diabetes"
}
```

**Response:**

```json
{
    "status": "success",
    "test_content": "Patient has diabetes with elevated HbA1c. Starting metformin and insulin therapy.",
    "topic_hint": "diabetes",
    "references_found": 2,
    "references": [
        {
            "title": "Diabetes Management Guidelines",
            "topic": "diabetes",
            "id": 1
        },
        {
            "title": "Metformin Therapy",
            "topic": "diabetes",
            "id": 2
        }
    ],
    "message": "Found 2 clinical references for the given content"
}
```

## Summary Types

- `medical_record`: General medical record summary
- `encounter`: Patient encounter/visit summary
- `lab_results`: Laboratory results summary
- `medications`: Medication-focused summary

## Background Processing

The application uses Celery for background processing. Make sure Redis is configured and Celery worker is running:

```bash
# Start Celery worker
celery -A config worker --loglevel=info
```

## Code Examples

### Using the Service Directly

```python
from ai_summarizer.services import OpenAIService

# Initialize service
ai_service = OpenAIService()

# Generate summary
summary = ai_service.generate_summary(
    content="Patient medical data...",
    context="Patient context...",
    summary_type="encounter"
)
```

### Using Background Task

```python
from ai_summarizer.tasks import create_summary_with_references

# Create summary asynchronously
task_result = create_summary_with_references.delay(
    patient_id=1,
    content="Medical data...",
    context="Patient context...",
    summary_type="encounter",
    topic_hint="diabetes"
)
```

## Features

- ✅ GapGPT API integration with OpenAI fallback
- ✅ Specialized medical prompts for different summary types
- ✅ Background processing with Celery
- ✅ **Clinical reference linking** - Automatically links relevant clinical references based on summary content and keywords
- ✅ Generic foreign key support for linking to any model
- ✅ Comprehensive REST API with DRF
- ✅ API documentation with drf-spectacular
- ✅ Error handling and logging
- ✅ Statistics and monitoring endpoints
- ✅ Admin interface with clinical references management

## Authentication

All endpoints require authentication. Use JWT tokens:

```bash
# Get token
POST /api/token/
{
    "username": "your_username",
    "password": "your_password"
}

# Use token in requests
Authorization: Bearer your_access_token_here
```

## Error Handling

The system includes robust error handling:

- Falls back to content truncation if AI service is unavailable
- Logs all errors for debugging
- Provides clear error messages in API responses
- Supports both GapGPT and OpenAI APIs for redundancy
