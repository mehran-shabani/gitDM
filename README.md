# GitDM - Diabetes Management System

**GitDM** (Git Diabetes Management) is a comprehensive diabetes management platform built with Django 5 and Django REST Framework. It provides healthcare professionals with advanced tools for patient data management, clinical decision support, AI-powered insights, and pattern analysis for diabetes care.

## 🎯 Project Overview

### Purpose
GitDM addresses the critical need for integrated diabetes management by providing healthcare professionals with a unified platform to:
- Track patient health data over time
- Identify patterns and anomalies in diabetic care
- Generate AI-powered clinical insights
- Manage medication prescriptions and clinical references
- Provide intelligent reminders and alerts

### Goals
- **Improve Patient Outcomes**: Enable proactive diabetes management through data-driven insights
- **Enhance Clinical Efficiency**: Streamline workflows for healthcare providers
- **Reduce Complications**: Early detection of concerning patterns and trends
- **Support Evidence-Based Care**: Integration with clinical references and guidelines

### Market Need
Diabetes affects millions globally, requiring continuous monitoring and management. Traditional paper-based or fragmented digital systems fail to provide the comprehensive view needed for optimal care. GitDM fills this gap by offering:
- Integrated patient timelines
- AI-powered pattern recognition
- Automated clinical alerts
- Version-controlled patient data
- Comprehensive analytics and reporting

## 🛠️ Technology Stack

### Backend Framework
- **Django 5.0+**: Modern Python web framework with robust ORM and security features
- **Django REST Framework 3.15+**: Powerful toolkit for building Web APIs
- **PostgreSQL/SQLite**: Primary database (SQLite for development, PostgreSQL for production)

### Authentication & Security
- **JWT Authentication**: Token-based authentication using `djangorestframework-simplejwt`
- **Role-Based Access Control**: Custom permission system for doctors, patients, and administrators
- **Security Middleware**: Custom audit logging and security enhancements

### AI & Analytics
- **OpenAI API**: GPT-powered clinical summarization and insights
- **NumPy & Pandas**: Statistical analysis and data processing
- **Pattern Analysis**: Custom anomaly detection algorithms
- **Matplotlib & Seaborn**: Data visualization for analytics

### Documentation & API
- **OpenAPI 3.0**: Complete API specification with Swagger UI
- **drf-spectacular**: Automated API schema generation
- **ReDoc**: Alternative API documentation interface

### Task Processing
- **Celery**: Asynchronous task processing for AI operations
- **Django-Celery-Beat**: Periodic task scheduling for reminders and analytics

### Development & Deployment
- **Docker**: Containerized development and deployment
- **GitHub Codespaces**: Cloud development environment support
- **Gunicorn**: Production WSGI server
- **pytest**: Comprehensive testing framework

### Reporting & Export
- **ReportLab**: PDF generation for clinical reports
- **OpenPyXL**: Excel export functionality
- **Matplotlib**: Chart generation for analytics

## 💡 Why GitDM?

### Unique Value Proposition
1. **Medical Domain Expertise**: Built specifically for diabetes care workflows
2. **AI Integration**: Leverages modern AI for clinical insights and pattern detection
3. **Comprehensive Timeline**: Unified view of all patient interactions and data
4. **Version Control**: Git-inspired versioning for medical data integrity
5. **Persian Language Support**: Localized for Persian-speaking healthcare providers

### Technical Advantages
- **Modern Django Architecture**: Leverages latest Django features and best practices
- **Microservice-Ready**: Modular app structure enables easy scaling
- **API-First Design**: RESTful APIs enable integration with external systems
- **Security-Focused**: Built-in audit trails and role-based permissions
- **Cloud-Native**: Docker-based deployment with Codespaces support

## 📋 Usage Scenario

### Typical Workflow

1. **Doctor Login**: Healthcare provider authenticates using email/password
2. **Patient Management**: View patient list, create new patient profiles
3. **Clinical Encounters**: Record SOAP-structured clinical visits
4. **Lab Results**: Input laboratory test results with LOINC coding
5. **Medication Orders**: Prescribe medications with ATC coding
6. **AI Insights**: Generate AI-powered summaries of patient status
7. **Pattern Analysis**: Review automated anomaly detection alerts
8. **Timeline Review**: Examine comprehensive patient timeline
9. **Clinical References**: Access integrated clinical guidelines and references

### Example User Journey

```
Doctor logs in → Views dashboard with pending alerts → 
Selects patient → Reviews timeline → Records new encounter → 
Orders lab tests → Prescribes medication → Generates AI summary → 
Reviews pattern analysis alerts → Sets follow-up reminders
```

### Key Features in Action
- **Smart Reminders**: Automated notifications for medication adherence and lab tests
- **Anomaly Detection**: Statistical analysis identifies concerning trends
- **Clinical Decision Support**: AI-powered insights and reference integration
- **Comprehensive Reporting**: Export patient data and analytics reports
- **Version Control**: Track all changes with ability to revert modifications

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (recommended)
- Git

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gitdm
   ```

2. **Environment setup**
   ```bash
   # Copy environment template (if available)
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run bootstrap script**
   ```bash
   ./bootstrap.sh
   ```

4. **Access the application**
   - Application: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs/
   - Admin Panel: http://localhost:8000/admin
   - Default admin credentials: `admin` / `admin123`

### GitHub Codespaces Setup

The project includes full GitHub Codespaces support:
1. Open in Codespaces
2. Automatic setup runs (SQLite database, migrations, static files)
3. Access via port-forwarded URL on port 8000

### Local Development (Without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database setup**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - defaults to SQLite)
POSTGRES_DB=diabetes
POSTGRES_USER=diabetes
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432

# Redis (Optional - for Celery)
REDIS_URL=redis://your-redis-host:6379/0

# AI Services
OPENAI_API_KEY=your-openai-api-key
GAPGPT_API_KEY=your-gapgpt-api-key

# MinIO (Optional - for file storage)
MINIO_ENDPOINT=your-minio-host:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_USE_HTTPS=False
MINIO_MEDIA_BUCKET=media
MINIO_STATIC_BUCKET=static
```

## 🏗️ Project Architecture

### Application Structure

```
config/          # Django project settings and URL configuration
gitdm/           # Core domain (users, patients, authentication)
encounters/      # Clinical encounters and SOAP notes
laboratory/      # Lab results and LOINC coding
pharmacy/        # Medication orders and ATC coding
references/      # Clinical references and guidelines
intelligence/    # AI summaries and pattern analysis
analytics/       # Advanced analytics and anomaly detection
notifications/   # Alert and notification system
reminders/       # Smart reminder system
timeline/        # Patient timeline visualization
versioning/      # Data versioning and audit trails
security/        # Security middleware and permissions
gateway/         # API routing and gateway services
tests/           # Comprehensive test suite
```

### Key Models

- **User**: Custom user model with doctor/patient roles
- **PatientProfile**: Comprehensive patient information
- **DoctorProfile**: Healthcare provider profiles with specializations
- **Encounter**: Clinical visits with SOAP structure
- **LabResult**: Laboratory test results with LOINC codes
- **MedicationOrder**: Prescription management with ATC codes
- **AISummary**: AI-generated clinical insights
- **BaselineMetrics**: Statistical baselines for anomaly detection

## 🔗 API Documentation

### Core Endpoints

All API endpoints are prefixed with `/api/` and require JWT authentication (except authentication endpoints).

#### Authentication
- `POST /api/token/` - Obtain JWT access/refresh tokens
- `POST /api/token/refresh/` - Refresh access token

#### Patient Management
- `GET /api/patients/` - List patients (filtered by doctor access)
- `POST /api/patients/` - Create new patient
- `GET /api/patients/{id}/` - Patient details
- `PUT/PATCH /api/patients/{id}/` - Update patient
- `DELETE /api/patients/{id}/` - Delete patient
- `GET /api/patients/{id}/timeline/` - Patient timeline (limit: max 500)

#### Clinical Data
- `GET/POST /api/encounters/` - Clinical encounters
- `GET/POST /api/labs/` - Laboratory results
- `GET/POST /api/meds/` - Medication orders
- `GET/POST /api/refs/` - Clinical references

#### AI & Analytics
- `GET/POST /api/ai-summaries/` - AI-generated summaries
- `POST /api/ai-summaries/{id}/regenerate/` - Regenerate summary
- `GET /api/pattern-analyses/` - Pattern analysis results
- `POST /api/pattern-analyses/analyze/` - Request new analysis
- `GET /api/anomaly-detections/` - Detected anomalies
- `GET /api/baseline-metrics/` - Patient baseline metrics

#### System Features
- `GET /api/versions/{resource_type}/{resource_id}/` - Version history
- `POST /api/versions/{resource_type}/{resource_id}/revert/` - Revert to version
- `GET /api/export/patient/{id}/` - Export patient data
- `GET /health/` - System health check

### API Documentation Interfaces
- **Swagger UI**: `/api/docs/` - Interactive API documentation
- **ReDoc**: `/api/redoc/` - Alternative documentation interface
- **OpenAPI Schema**: `/api/schema/` - Raw OpenAPI specification

For detailed API documentation including request/response schemas, parameters, and examples, see [API.md](API.md).

## 🧪 Testing

Run the test suite:
```bash
pytest -v
```

The test suite includes:
- API endpoint testing
- JWT authentication flows
- Versioning system validation
- Health check verification
- Model validation tests

## 🚀 Deployment Notes

### Docker Deployment
The application is containerized and ready for deployment:
- `Dockerfile` provides production-ready container
- `docker-compose.yml` for local development
- Environment variable configuration
- Static file collection and database migration automation

### Production Considerations
- Set `DJANGO_DEBUG=False` in production
- Configure PostgreSQL database
- Set up Redis for Celery task processing
- Configure MinIO or AWS S3 for file storage
- Set secure `DJANGO_SECRET_KEY`
- Configure proper `DJANGO_ALLOWED_HOSTS`

### Scaling Options
- Horizontal scaling with multiple Django instances
- Separate Celery workers for AI processing
- Database read replicas for analytics
- CDN integration for static files

## 📁 Key Features

### 🤖 AI-Powered Insights
- Automated clinical summary generation
- Pattern recognition in patient data
- Clinical reference integration
- Intelligent content analysis

### 📊 Advanced Analytics
- Statistical baseline calculations
- Anomaly detection algorithms
- Trend analysis and forecasting
- Performance metrics and reporting

### 🔔 Smart Notifications
- Medication adherence reminders
- Lab test scheduling alerts
- Clinical milestone notifications
- Customizable alert thresholds

### 📈 Patient Timeline
- Comprehensive chronological view
- Interactive data visualization
- Multi-source data integration
- Exportable patient summaries

### 🔒 Security & Compliance
- Role-based access control
- Comprehensive audit logging
- Data versioning and recovery
- Secure API authentication

### 🌐 Integration Ready
- RESTful API design
- OpenAPI 3.0 specification
- Webhook support for notifications
- Export capabilities for external systems

## 📜 License

This project is released under the license specified in the `LICENSE` file.

## 🤝 Contributing

### Development Guidelines
- Run tests before submitting PRs: `pytest -v`
- Follow PEP 8 style guidelines (enforced by Ruff)
- Keep commit messages concise and descriptive
- Submit focused, small pull requests
- Ensure all new features include appropriate tests

### Code Quality
- Ruff linting and formatting configured
- Type hints required for new code
- Comprehensive test coverage expected
- Documentation updates for new features

---

*For detailed API documentation, see [API.md](API.md)*
*For deployment guides and advanced configuration, refer to the deployment documentation*