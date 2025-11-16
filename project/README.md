# Contract Refund Eligibility System

Full-stack application for processing and managing GAP insurance contract refunds with AI-powered data extraction.

## Quick Start

### Start All Services

```bash
# Start everything (backend, frontend, database)
./start.sh

# Start with database seeding
./start.sh --seed

# Start backend only
./start.sh --backend-only
```

### Stop All Services

```bash
# Stop backend and frontend (keep Docker running)
./stop.sh

# Stop everything including Docker
./stop.sh --all
```

## Services

Once started, the following services will be available:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Next.js web application |
| **Backend API** | http://localhost:8001 | FastAPI REST API |
| **API Docs** | http://localhost:8001/docs | Interactive Swagger UI |
| **ReDoc** | http://localhost:8001/redoc | Alternative API documentation |
| **PostgreSQL** | localhost:5432 | Database (postgres/postgres) |
| **Redis** | localhost:6379 | Cache (not yet implemented) |

## Prerequisites

Before running the startup scripts, ensure you have:

- **Docker & Docker Compose** - For PostgreSQL and Redis
- **UV** - Python package manager ([install](https://github.com/astral-sh/uv))
- **Node.js & npm** - For frontend (v18+ recommended)
- **Python 3.12+** - For backend

## Project Structure

```
project/
├── start.sh              # Start all services
├── stop.sh               # Stop all services
├── backend/              # FastAPI backend
│   ├── app/              # Application code
│   ├── tests/            # Test suite
│   ├── scripts/          # Utility scripts
│   └── docker-compose.yml # Docker services
└── frontend/             # Next.js frontend
    ├── app/              # Next.js app directory
    ├── components/       # React components
    └── __tests__/        # Test suite
```

## Development Workflow

### Initial Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd project

# 2. Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# 3. Install backend dependencies (automatically done by start.sh)
cd backend
uv sync --all-extras

# 4. Install frontend dependencies (automatically done by start.sh)
cd frontend
npm install

# 5. Start all services with database seeding
cd ..
./start.sh --seed
```

### Daily Development

```bash
# Start services
./start.sh

# View logs
tail -f /tmp/backend.log
tail -f /tmp/frontend.log

# Stop services when done
./stop.sh
```

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
cd frontend
npm run test:e2e
```

## Script Options

### start.sh Options

| Option | Description |
|--------|-------------|
| `--seed` | Seed database with test data (15 contracts, 5 extractions) |
| `--backend-only` | Start backend only, skip frontend |
| `--help` | Show help message |

**Examples:**

```bash
# Standard startup
./start.sh

# Startup with fresh test data
./start.sh --seed

# Backend development only
./start.sh --backend-only
```

### stop.sh Options

| Option | Description |
|--------|-------------|
| `--all` or `-a` | Stop everything including Docker services |
| `--help` or `-h` | Show help message |

**Examples:**

```bash
# Stop backend and frontend (keep Docker running)
./stop.sh

# Stop everything including database
./stop.sh --all
```

## Manual Service Management

If you prefer to start services manually:

### Backend

```bash
cd backend

# Start Docker services
docker-compose up -d

# Start backend API
uv run uvicorn app.main:app --reload --port 8001

# Seed database (optional)
uv run python scripts/seed_db.py --with-extractions
```

### Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

## Troubleshooting

### Port Conflicts

If you see "Address already in use" errors:

```bash
# Kill processes on specific ports
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8001 | xargs kill -9  # Backend

# Or use the stop script
./stop.sh
```

### Database Connection Issues

```bash
# Check if Docker services are running
cd backend
docker-compose ps

# Restart Docker services
docker-compose restart postgres redis

# Check database connection
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "SELECT 1"
```

### Logs

View service logs:

```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log

# Docker logs
cd backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Clean Restart

To completely reset everything:

```bash
# 1. Stop all services
./stop.sh --all

# 2. Remove Docker volumes (⚠️ deletes all data)
cd backend
docker-compose down -v

# 3. Start fresh
cd ..
./start.sh --seed
```

## API Quick Reference

### Health Check

```bash
curl http://localhost:8001/health
```

### Search for Contract

```bash
curl -X POST http://localhost:8001/api/v1/contracts/search \
  -H "Content-Type: application/json" \
  -d '{"account_number": "ACC-TEST-00001"}'
```

### Get Contract by ID

```bash
curl http://localhost:8001/api/v1/contracts/GAP-2024-0001
```

### Interactive API Testing

Visit http://localhost:8001/docs for Swagger UI where you can test all endpoints interactively.

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_refund_system
REDIS_URL=redis://localhost:6379/0

# LLM Provider
ANTHROPIC_API_KEY=your-api-key-here
LLM_PROVIDER=anthropic

# Application
APP_ENV=development
DEBUG=true
```

### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api/v1

# Auth0 (when implemented)
# AUTH0_DOMAIN=your-domain.auth0.com
# AUTH0_CLIENT_ID=your-client-id
```

## Documentation

- **Backend**: See `backend/LOCAL_SETUP.md` for detailed backend setup
- **Frontend**: See `frontend/README.md` for detailed frontend setup
- **API Docs**: http://localhost:8001/docs (when running)
- **Day Completion**: See `backend/DAY_*_COMPLETE.md` for implementation history

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs (`/tmp/backend.log`, `/tmp/frontend.log`)
3. Check Docker logs (`docker-compose logs`)
4. Refer to detailed setup guides in `backend/` and `frontend/` directories

## Development Status

- ✅ **Day 1-4**: Complete (Database, Models, Schemas, Contract API)
- 🚧 **Day 5**: In Progress (LLM Integration)
- ⏳ **Days 6-12**: Pending (Extraction Workflow, PDF Processing, Chat, Auth, etc.)

---

**Quick Start**: `./start.sh --seed`

**Stop Services**: `./stop.sh`

**View Logs**: `tail -f /tmp/backend.log /tmp/frontend.log`
