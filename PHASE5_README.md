# Phase 5 - AI Integration & Processing

## Overview
This phase implements AI-powered summarization of patient records using OpenAI's GPT-4o-mini model. When new Encounters, Lab Results, or Medication Orders are created, they automatically trigger AI summarization tasks via Celery.

## Architecture
- **Event Triggering**: Django post_save signals on Encounter/Lab/Medication models
- **Task Queue**: Celery with Redis broker for async processing  
- **AI Integration**: OpenAI ChatCompletion API (gpt-4o-mini)
- **Storage**: AISummary model with links to ClinicalReference
- **Error Handling**: Retry mechanism with exponential backoff

## Setup Instructions

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Docker Setup
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 3. Testing the AI Integration
```bash
# Run tests
docker-compose exec web pytest tests/

# Create test data via Django admin
# Visit http://localhost:8000/admin
# Create a Patient, then an Encounter - AI summary should be generated automatically
```

## Components

### Django Apps
- `patients_core`: Patient model and core functionality
- `diab_encounters`: Encounter model with SOAP notes
- `diab_labs`: Laboratory results with LOINC codes
- `diab_medications`: Medication orders
- `ai_summarizer`: AI summary generation and storage
- `clinical_refs`: Clinical reference materials

### Key Files
- `ai_summarizer/tasks.py`: Celery task for OpenAI integration
- `*/signals.py`: Django signals for automatic AI triggering
- `ai_summarizer/models.py`: AISummary model with clinical references

### Celery Services
- **worker**: Processes AI summarization tasks
- **beat**: Scheduler for periodic tasks (if needed)

## Usage
1. Create a new Encounter, Lab Result, or Medication Order via Django admin
2. The system automatically triggers AI summarization
3. Check the AISummary model for the generated summary
4. AI summaries are linked to relevant ClinicalReference objects

## Monitoring
- Check Celery worker logs: `docker-compose logs worker`
- Monitor Redis queue: `docker-compose exec redis redis-cli monitor`
- View AI summaries in Django admin: `/admin/ai_summarizer/aisummary/`