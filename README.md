# FlowSketch

> From messy notes to perfectly synced diagrams, specs, and test plans — in minutes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/your-org/flowsketch)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-org/flowsketch/releases)

## 🚀 What is FlowSketch?

FlowSketch revolutionizes how teams turn unstructured requirements into production-ready documentation. Simply paste your meeting notes, Slack messages, or brainstorming ideas, and watch as AI transforms them into synchronized diagrams, specifications, and test plans.

### The Problem We Solve

Teams waste countless hours manually translating scattered requirements into:
- Technical diagrams
- Product specifications
- Acceptance criteria
- Test plans

This manual process is slow, error-prone, and becomes outdated the moment requirements change.

### Our Solution

FlowSketch automates this entire workflow:
1. **Paste** unstructured text
2. **Generate** diagrams, specs, and tests automatically
3. **Edit** either the diagram or spec — both stay in sync
4. **Export** professional documentation ready for stakeholders

---

## ✨ Key Features

### 🎯 Intelligent Text Analysis
- **Smart Entity Extraction**: AI identifies key components, actions, and relationships
- **Auto-Diagram Selection**: Chooses optimal diagram type (flowcharts, ERDs, sequence diagrams)
- **Context-Aware Processing**: Understands domain-specific terminology

### 🔄 Bidirectional Synchronization
- **Visual → Text**: Edit diagrams, specs update instantly
- **Text → Visual**: Modify specs, diagrams reflect changes
- **Conflict Resolution**: Smart merging when both are edited simultaneously

### 📋 Comprehensive Documentation Generation
- **Living Specifications**: Markdown docs that evolve with your diagrams
- **Acceptance Criteria**: Auto-generated test conditions for each feature
- **Runnable Tests**: Unit and integration test scaffolds in your preferred language

### 🎨 Professional Export Options
- **Diagrams**: PNG, SVG, PDF, Mermaid syntax
- **Documentation**: Markdown, Word, PDF formats
- **Shareable Links**: Public read-only URLs for stakeholder review

### 🔧 Developer-Friendly Integrations
- **Project Management**: Push to Jira, Trello, Linear, Asana
- **Version Control**: Export specs as docs for your repo
- **API Documentation**: Generate OpenAPI specs from service diagrams

---

## 🎯 Who Uses FlowSketch?

### Product Managers
Transform meeting notes into user flows and feature specifications that engineering teams can immediately act on.

### Software Engineers
Convert architecture discussions into system diagrams with accompanying API documentation and test plans.

### Business Analysts
Create process flows and requirement documents from stakeholder interviews and business rules.

### Startup Founders
Generate MVP specifications and technical roadmaps without needing dedicated technical writers or designers.

### Consultants & Agencies
Deliver professional documentation and diagrams to clients in a fraction of the traditional time.

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.9+
- PostgreSQL 12+
- Redis (optional, for background tasks)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/flowsketch.git
cd flowsketch

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Django configuration

# Run database migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start the development servers
cd ../frontend && npm run dev &
cd ../backend && python manage.py runserver
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/flowsketch
REDIS_URL=redis://localhost:6379

# Django Settings
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# AI Services
KIRO_API_KEY=your_kiro_api_key
OPENAI_API_KEY=your_openai_key  # fallback option

# File Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=flowsketch-exports

# CORS Settings (for frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🏗️ Architecture

### Tech Stack

**Frontend**
- **React 18 or Next.js 14** with TypeScript for type-safe UI components
- **Tailwind CSS** for rapid, consistent styling
- **XState** for managing complex diagram interaction states
- **elkjs** for automatic graph layout algorithms
- **React Query / SWR** for efficient server state management
- **Next.js API Routes** (if using Next.js) for serverless functions

**Backend**
- **Django 5.0** with Django REST Framework for robust API endpoints
- **PostgreSQL** with Django ORM for reliable data persistence
- **Celery + Redis** for background processing of large diagrams
- **Django CORS Headers** for frontend integration
- **Django Channels** (optional) for real-time collaboration

**AI & Processing**
- **Kiro AI** for intelligent spec and test generation
- **spaCy** for natural language entity extraction
- **LangChain** for orchestrating complex AI workflows
- **Mermaid.js** for diagram syntax generation

### System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ React/Next.js   │────│  Django + DRF    │────│   PostgreSQL   │
│    Client       │    │     Server       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│   AI Services    │─────────────┘
                        │  (Kiro, spaCy)   │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │ Celery + Redis   │
                        │ (Background Jobs)│
                        └──────────────────┘
```

---

## 📚 Usage Examples

### Basic Workflow

```python
# Example: Converting user story to diagram
user_input = """
When a user logs in, they see the dashboard.
From dashboard, they can create a new report.
The system generates a PDF and emails it to the user.
"""

# FlowSketch automatically generates:
# 1. Flowchart with 4 connected nodes
# 2. Specification with acceptance criteria
# 3. Test cases for each step
```

### API Usage

```javascript
// Create a new project
const project = await fetch('/api/v1/projects/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    name: 'User Onboarding Flow',
    description: user_input,
    diagram_type: 'auto' // or 'flowchart', 'erd', 'sequence'
  })
});

// Generate diagram and spec
const result = await fetch(`/api/v1/projects/${project.id}/generate/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token
  }
});
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get started:

### Development Setup

```bash
# Fork the repository and clone your fork
git clone https://github.com/your-username/flowsketch.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and add tests
npm test  # Run frontend tests
pytest    # Run backend tests

# Submit a pull request
```

### Code Style

- **Frontend**: We use Prettier and ESLint with TypeScript strict mode
- **Backend**: Black formatting with flake8 linting
- **Commits**: Follow [Conventional Commits](https://conventionalcommits.org/)

### Testing

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python manage.py test

# Run tests with coverage
cd backend && coverage run --source='.' manage.py test
cd backend && coverage report

# Integration tests
docker-compose -f docker-compose.test.yml up
```

---

## 📈 Roadmap

### Phase 1: Core MVP (Current)
- [x] Text-to-diagram generation
- [x] Basic bidirectional sync
- [x] Export functionality
- [ ] User authentication
- [ ] Project sharing

### Phase 2: Enhanced Intelligence (Q2 2024)
- [ ] Multi-language test generation
- [ ] Advanced diagram types (BPMN, UML)
- [ ] Real-time collaborative editing
- [ ] Version history and branching

### Phase 3: Enterprise Features (Q3 2024)
- [ ] SSO integration
- [ ] Advanced project management hooks
- [ ] Custom AI model training
- [ ] On-premise deployment options

### Phase 4: Platform Expansion (Q4 2024)
- [ ] Mobile app
- [ ] Plugin ecosystem
- [ ] API marketplace
- [ ] White-label solutions

---

## 💼 Customer Acquisition Strategy

### Early Adopter Program

We're seeking beta users who can provide feedback and case studies:

**What we offer:**
- Free access during beta period
- Direct line to our development team
- Co-marketing opportunities
- Custom feature development consideration

**What we need:**
- Regular feedback on UX and feature gaps
- Permission to use anonymized case studies
- Referrals to other potential users in your network

**Apply for early access**: [beta@flowsketch.com](mailto:beta@flowsketch.com)

### Target Customer Segments

1. **SaaS Startups (0-50 employees)**
   - Pain: Manual documentation processes slow down product development
   - Solution: Automated spec generation accelerates feature delivery

2. **Digital Agencies (10-100 employees)**
   - Pain: Client deliverables require significant documentation overhead
   - Solution: Professional diagrams and specs generated in minutes, not hours

3. **Enterprise Dev Teams (100+ employees)**
   - Pain: Requirements often get lost in translation between stakeholders
   - Solution: Single source of truth that keeps everyone aligned

### Go-to-Market Channels

- **Product Hunt launch** for initial visibility
- **Developer community engagement** (Reddit, Hacker News, Dev.to)
- **Content marketing** with technical tutorials and case studies
- **Integration partnerships** with project management tools
- **Conference presentations** at product and development events

---

## 🔒 Security & Privacy

- **Data Encryption**: All data encrypted in transit and at rest
- **Privacy by Design**: User data is never used to train AI models
- **SOC 2 Compliance**: Currently pursuing Type 2 certification
- **GDPR Ready**: Full data portability and deletion capabilities

---

## 📞 Support & Community

### Getting Help
- **Documentation**: [docs.flowsketch.com](https://docs.flowsketch.com)
- **Community Forum**: [community.flowsketch.com](https://community.flowsketch.com)
- **Email Support**: [support@flowsketch.com](mailto:support@flowsketch.com)
- **Live Chat**: Available in-app during business hours

### Stay Connected
- **Twitter**: [@FlowSketchApp](https://twitter.com/FlowSketchApp)
- **LinkedIn**: [FlowSketch](https://linkedin.com/company/flowsketch)
- **Discord**: [Join our community](https://discord.gg/flowsketch)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Kiro AI** for powering our intelligent generation capabilities
- **The Open Source Community** for the incredible tools that make FlowSketch possible
- **Our Beta Users** for their invaluable feedback and patience

---

*Made with ❤️ by the FlowSketch team*

**Ready to transform your workflow?** [Start your free trial today →](https://app.flowsketch.com/signup)