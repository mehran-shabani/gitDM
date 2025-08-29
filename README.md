# GitDM - Diabetes Management System

A version control system for diabetes patients from prediabetes, diabetes management, treatment, and reducing adverse effects and organopathy control through smart AI agents and cross-platform solutions. This is a segment of the Med3 project from the Helssa healthcare platform.

## 📁 Project Structure

```
/
├── doc/                          # Documentation organized by phases
│   ├── phase1/                   # Setup & Infrastructure
│   ├── phase2/                   # Data Models & Relationships
│   ├── phase3/                   # Versioning & Append-only Design
│   ├── phase4/                   # API & Authentication
│   ├── phase5/                   # AI Integration & Processing
│   ├── phase6/                   # Clinical References & Knowledge
│   ├── phase7/                   # Security & RBAC
│   └── phase8/                   # Testing & Integration Flow
├── cursoragent/                  # AI Agent configurations
├── gemini/                       # Gemini AI agent setup
├── examples/                     # Example configurations and outputs
├── .ai-review-config.yaml        # AI review configuration
├── .coderabbitai.yaml           # CodeRabbit AI configuration
└── AI-AGENTS-README.md          # AI agents documentation
```

## 🎯 Phase Documentation Structure

Each phase directory (`doc/phase1/` through `doc/phase8/`) contains:
- `should-*.md` files: Implementation requirements and specifications
- `suggestion-*.md` files: Optional recommendations and best practices
- `AGENT.MD`: Phase-specific AI agent instructions
- Log files and build reports
- Review summaries and compatibility reports

## 🤖 AI Review System

This project uses automated AI review agents for code quality and architecture compliance:

- **CodeRabbit**: Technical code review and compliance checking
- **Gemini**: High-level architecture analysis and strategic recommendations

### Configuration Files:
- `.ai-review-config.yaml`: General AI review settings
- `.coderabbitai.yaml`: CodeRabbit-specific configuration
- `gemini/gemini.md`: Gemini agent instructions

## 🔗 Helssa Integration

This project is designed as a continuation of the Helssa healthcare platform, ensuring:
- **Namespace Compatibility**: All components follow Helssa naming conventions
- **API Consistency**: Endpoints and data structures align with existing Helssa APIs
- **Migration Safety**: Backward compatibility with existing Helssa data
- **Security Model**: Integration with Helssa's RBAC and audit systems

## 📋 Development Workflow

1. **Phase-based Development**: Each feature is developed in phases (phase1-phase8)
2. **AI-Assisted Review**: All pull requests are automatically reviewed by AI agents
3. **Documentation-Driven**: Implementation follows `should-*.md` specifications
4. **Helssa Compliance**: All changes maintain compatibility with the Helssa platform

## 🚀 Getting Started

1. Review the phase documentation in `/doc/phase1/` to understand the project setup
2. Check AI agent configurations in `/cursoragent/` and `/gemini/`
3. Follow the implementation guidelines in phase-specific `should-*.md` files
4. Ensure all changes maintain Helssa compatibility standards

## 🔐 Authentication & User Management

This application uses JWT authentication with admin-only user creation:

- No public signup: users are created through the Django admin panel.
- JWT tokens: obtain via `/api/token/` and refresh via `/api/token/refresh/`.
- Secure by design: no public user registration endpoints exist.
- Admin control: full user lifecycle via Django admin.

For details, see `/doc/phase4/authentication-guide.md`.
## 📝 Contributing

- All development should follow the phase-based approach
- Reference the appropriate `should-*.md` files for implementation requirements
- AI agents will review all pull requests for compliance
- Maintain compatibility with Helssa platform standards
- Set up pre-commit hooks before contributing (see `docs/development/pre-commit.md`)

## 📖 Additional Documentation

- **AI Agents**: See `AI-AGENTS-README.md` for detailed AI review system documentation
- **Examples**: Check `/examples/` for sample configurations and outputs
- **Phase Details**: Each `/doc/phaseX/` directory contains comprehensive phase documentation