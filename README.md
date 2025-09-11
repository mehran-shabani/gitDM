# GitDM - Diabetes Management System

**GitDM** (Git Diabetes Management) is a comprehensive diabetes management platform built with Django 5 and Django REST Framework. It provides healthcare professionals with advanced tools for patient data management, clinical decision support, AI-powered insights, and pattern analysis for diabetes care.

> **Note:** All project documentation is consolidated here. The former `docs.md` file has been removed.

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

```m
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

**Required:**
- Python 3.13+
- Node.js 20+ (for frontend)
- Git

**Optional (for Docker):**
- Docker and Docker Compose

### Quick Start Options

Choose the setup method that best fits your needs:

#### Option 1: Local Development (Recommended for Development)

**Best for:** Active development, debugging, IDE integration

```bash
# 1. Clone the repository
git clone <repository-url>
cd gitdm

# 2. Run the setup script
./scripts/setup-dev.sh

# 3. Start development servers
./scripts/start-dev.sh
```

**What you get:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Admin: http://localhost:8000/admin (admin/admin123)

#### Option 2: Simple Docker Setup

**Best for:** Quick testing, consistent environment

```bash
# 1. Clone and setup
git clone <repository-url>
cd gitdm

# 2. Start with Docker (SQLite)
./scripts/start-simple.sh
```

**What you get:**
- Backend: http://localhost:8000 (SQLite database)

#### Option 3: Full Docker Setup

**Best for:** Production-like environment, full feature testing

```bash
# 1. Clone and setup
git clone <repository-url>
cd gitdm

# 2. Start full stack
./scripts/start-advanced.sh
```

**What you get:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

#### Option 4: GitHub Codespaces

**Best for:** Cloud development, no local setup needed

1. Click "Open in Codespaces" on GitHub
2. Wait for automatic setup (2-3 minutes)
3. Access the application through forwarded ports

### Detailed Setup Instructions

#### Local Development Setup

1. **Clone and navigate**
   ```bash
   git clone <repository-url>
   cd gitdm
   ```

2. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (optional for development)
   ```

3. **Backend setup**
   ```bash
   # Create virtual environment
   python -m venv backend/venv
   source backend/venv/bin/activate  # Windows: backend\venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r backend/requirements.txt
   
   # Database setup
   python manage.py migrate
   python manage.py createsuperuser  # Optional: create your own admin
   python manage.py collectstatic --noinput
   ```

4. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. **Start development**
   ```bash
   # Option A: Both servers simultaneously
   ./scripts/start-dev.sh
   
   # Option B: Separate terminals
   ./scripts/start-backend.sh    # Terminal 1
   ./scripts/start-frontend.sh   # Terminal 2
   ```

#### Docker Setup

1. **Simple setup (SQLite)**
   ```bash
   git clone <repository-url>
   cd gitdm
   ./scripts/start-simple.sh
   ```

2. **Advanced setup (PostgreSQL + Redis)**
   ```bash
   git clone <repository-url>
   cd gitdm
   ./scripts/start-advanced.sh
   ```

3. **Stop services**
   ```bash
   ./scripts/stop-simple.sh     # For simple setup
   ./scripts/stop-advanced.sh   # For advanced setup
   ```

### Environment Configuration

The project uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

**Key Configuration Options:**

```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - defaults to SQLite)
# POSTGRES_DB=gitdm
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432

# AI Services (Optional)
# OPENAI_API_KEY=your-openai-api-key

# Redis (Optional - for Celery)
# REDIS_URL=redis://localhost:6379/0
```

### GitHub Codespaces

The project includes complete Codespaces support with automatic setup:

1. **Open in Codespaces** from the GitHub repository
2. **Automatic setup** includes:
   - Python and Node.js environments
   - All dependencies installed
   - Database migrations
   - Admin user creation
   - Frontend build

3. **Access services:**
   - Backend: Port 8000 (auto-forwarded)
   - Frontend: Port 3000 (start manually with `cd frontend && npm run dev`)

4. **Default credentials:**
   - Admin: `admin` / `admin123`

### Troubleshooting

#### Common Issues

1. **Port already in use**
   ```bash
   # Find what's using the port
   lsof -i :8000
   # Kill the process or change port in settings
   ```

2. **Permission denied on scripts**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **Database issues**
   ```bash
   # Reset database (WARNING: deletes data)
   rm db.sqlite3
   python manage.py migrate
   ```

4. **Docker issues**
   ```bash
   # Clean up Docker
   docker system prune -f
   ./scripts/clean.sh  # Project cleanup script
   ```

5. **Frontend build errors**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

#### Health Check

Run the health check script to verify your setup:

```bash
./scripts/health-check.sh
```

This will check:
- Service availability (Django, React)
- Database connections
- Docker containers
- Environment setup

### Development Workflow

1. **Daily development:**
   ```bash
   ./scripts/start-dev.sh     # Start both servers
   # Develop in your IDE
   # Press Ctrl+C to stop
   ```

2. **Testing:**
   ```bash
   ./scripts/test.sh          # Run all tests
   ```

3. **Cleanup:**
   ```bash
   ./scripts/clean.sh         # Clean build artifacts
   ```

4. **Backup:**
   ```bash
   ./scripts/backup.sh        # Create project backup
   ```

### Project Structure

```
gitdm/
├── backend/              # Django backend application
│   ├── config/          # Django settings and configuration
│   ├── apps/            # Django applications (encounters, pharmacy, etc.)
│   └── requirements.txt # Backend dependencies
├── frontend/            # React frontend application
│   ├── src/            # React source code
│   ├── package.json    # Frontend dependencies
│   └── Dockerfile      # Frontend container config
├── scripts/            # Utility scripts
│   ├── setup-dev.sh   # Development setup
│   ├── start-*.sh     # Service startup scripts
│   └── README.md      # Scripts documentation
├── .devcontainer/      # GitHub Codespaces configuration
├── .github/           # GitHub workflows and templates
├── docker-compose*.yml # Docker configurations
├── Dockerfile         # Backend container config
└── requirements.txt   # Root Python dependencies
```

## 🏗️ Project Architecture

### Application Structure

```bash
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

```bash
- `GET /api/patients/` - List patients (filtered by doctor access)
- `POST /api/patients/` - Create new patient
- `GET /api/patients/{id}/` - Patient details
- `PUT/PATCH /api/patients/{id}/` - Update patient
- `DELETE /api/patients/{id}/` - Delete patient
- `GET /api/patients/{id}/timeline/` - Patient timeline (limit: max 500)
```

#### Clinical Data

- `GET/POST /api/encounters/` - Clinical encounters
- `GET/POST /api/labs/` - Laboratory results
- `GET/POST /api/meds/` - Medication orders
- `GET/POST /api/refs/` - Clinical references

### A-I & Analytics

```bash
- `GET/POST /api/ai-summaries/` - AI-generated summaries
- `POST /api/ai-summaries/{id}/regenerate/` - Regenerate summary
- `GET /api/pattern-analyses/` - Pattern analysis results
- `POST /api/pattern-analyses/analyze/` - Request new analysis
- `GET /api/anomaly-detections/` - Detected anomalies
- `GET /api/baseline-metrics/` - Patient baseline metrics
```

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
