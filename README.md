# DARKAGENTS 🚀

**Enterprise SaaS Platform Builder powered by 11 Specialized AI Agents**

DARKAGENTS is an AI agent orchestration platform that simulates a complete 11-person development team to automatically build production-ready SaaS applications. Watch your product being built in real-time through our NASA-style mission control dashboard.

## 🎯 Features

- **11 Specialized AI Agents**: Product Manager, System Architect, Backend Developer, UI/UX Designer, QA Engineer, Security Specialist, Frontend Developer, DevOps Engineer, Growth Marketer, Business Strategist, Platform Orchestrator
- **NASA-Style Dashboard**: Real-time visibility into every agent's activity
- **4-Agent Parallel Review**: Automated code review by PM, Architect, QA, and Security
- **Production-Ready Output**: Complete SaaS application with code, infrastructure, marketing, and financials
- **4 User Checkpoints**: Review and approve at key milestones

## 🏗️ Architecture

**Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis + LangChain
**Frontend**: Next.js 14 + React + TypeScript + Tailwind + Shadcn/UI
**AI**: Anthropic Claude Sonnet 4.5 via LangChain
**Deployment**: Railway (backend) + Vercel (frontend)

## 📦 Project Structure

```
darkagents/
├── backend/          # FastAPI backend
│   ├── agents/       # 11 AI agent implementations
│   ├── api/          # REST API routes
│   ├── database/     # SQLAlchemy models & migrations
│   ├── orchestrator/ # Agent workflow & state machine
│   └── services/     # Claude API, WebSocket, Storage
├── frontend/         # Next.js frontend
│   ├── app/          # Next.js 14 App Router
│   ├── components/   # React components
│   └── lib/          # Utilities & API client
└── shared/           # Shared TypeScript types
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (or SQLite for testing)
- Redis 7
- Anthropic API Key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Visit http://localhost:3000 to see the NASA dashboard.

## 📚 Documentation

- [Product Requirements Document](docs/PRD.md)
- [API Documentation](http://localhost:8000/docs) (when backend is running)
- [Agent Specifications](docs/agents.md)
- [Deployment Guide](docs/deployment.md)

## 🛣️ Development Roadmap

### Phase 1: MVP (Current - Months 1-2)
- ✅ Database schema and models
- ✅ User authentication
- 🚧 11 AI agents implementation
- 🚧 NASA dashboard with real-time updates
- 🚧 4-agent parallel review system
- ⬜ Deployment to Railway + Vercel

### Phase 2: Scale (Months 3-4)
- ⬜ Kubernetes deployment
- ⬜ Load testing integration
- ⬜ Multi-region deployment
- ⬜ Enhanced agent personalities

### Phase 3: Enterprise (Months 5-6)
- ⬜ Full microservices architecture
- ⬜ Enterprise compliance (SOC2, GDPR)
- ⬜ White-label option
- ⬜ Agent marketplace

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

This is currently a private project. Contact the team for collaboration opportunities.

## 📞 Support

For issues and questions, please open a GitHub issue or contact support@darkagents.com

---

**Built with ❤️ using Claude Code**
