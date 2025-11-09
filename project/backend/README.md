# Backend - Contract Refund Eligibility System

FastAPI backend for AI-powered contract extraction and review.

## Quick Start

### 1. Set Up Python Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual values
# Minimum required: DATABASE_URL, LLM API keys
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb contract_refund_system

# Run schema (one-time setup)
psql -U postgres -d contract_refund_system -f database/schema.sql

# Optional: Load seed data for development
psql -U postgres -d contract_refund_system -f database/seed/seed_data.sql
```

### 4. Run Application

```bash
# Development server with auto-reload
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings (Pydantic)
│   ├── database.py             # Database connection
│   ├── api/
│   │   └── v1/                 # API v1 endpoints
│   │       ├── contracts.py
│   │       ├── extractions.py
│   │       ├── chat.py
│   │       └── admin.py
│   ├── models/
│   │   └── database/           # SQLAlchemy models
│   ├── schemas/
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── repositories/           # Database access layer
│   ├── services/               # Business logic
│   ├── integrations/
│   │   └── llm_providers/      # LLM integrations
│   ├── middleware/             # Custom middleware
│   └── utils/                  # Utilities
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Pytest fixtures
├── database/                   # Database files
│   ├── schema.sql             # PostgreSQL schema
│   ├── seed/                  # Seed data
│   └── docs/                  # DB documentation
├── alembic/                   # Database migrations (TBD)
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Code Quality

```bash
# Format code with black
black app tests

# Lint with ruff
ruff check app tests

# Type checking with mypy
mypy app
```

### Database Migrations (Alembic - TBD)

```bash
# Create migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Endpoints

### Health & Status

- `GET /health` - Health check
- `GET /ready` - Readiness check

### Contracts (TBD)

- `POST /api/v1/contracts/search` - Search for contract
- `GET /api/v1/contracts/{contract_id}` - Get contract details

### Extractions (TBD)

- `POST /api/v1/extractions/{contract_id}/extract` - Extract data
- `GET /api/v1/extractions/{extraction_id}` - Get extraction
- `POST /api/v1/extractions/{extraction_id}/approve` - Approve extraction
- `POST /api/v1/extractions/{extraction_id}/reject` - Reject extraction
- `POST /api/v1/extractions/{extraction_id}/edit` - Edit/correct extraction

### Chat (TBD)

- `POST /api/v1/chat` - Send chat message

### Admin (TBD)

- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/users` - Create user
- `GET /api/v1/admin/metrics` - System metrics

## Environment Variables

See `.env.example` for all available environment variables.

### Required Variables

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
ANTHROPIC_API_KEY=sk-ant-...  # Or OPENAI_API_KEY
```

### Optional Variables

- `REDIS_URL` - Redis connection (default: localhost:6379)
- `LLM_PROVIDER` - LLM provider choice (openai, anthropic, bedrock)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)

## Testing Strategy

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions/classes
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Test multiple components together
   - Use test database
   - Test API endpoints end-to-end

### Test Markers

```python
@pytest.mark.unit         # Unit test
@pytest.mark.integration  # Integration test
@pytest.mark.slow         # Slow running test
@pytest.mark.db           # Requires database
@pytest.mark.redis        # Requires Redis
@pytest.mark.llm          # Calls LLM API (costs money)
@pytest.mark.external     # Requires external services
```

## Progress

### Completed ✅

- [x] FastAPI project structure
- [x] Configuration management (Pydantic Settings)
- [x] Health/readiness endpoints
- [x] Testing infrastructure (pytest)
- [x] Smoke tests passing
- [x] Database schema designed (see `database/`)

### In Progress 🚧

- [ ] SQLAlchemy models (Day 2)
- [ ] Alembic migrations
- [ ] API endpoints
- [ ] LLM integration

### Planned 📋

- [ ] Redis caching
- [ ] Chat interface
- [ ] Admin endpoints
- [ ] Comprehensive test coverage

## Troubleshooting

### Database Connection Issues

```bash
# Verify PostgreSQL is running
pg_isready

# Test connection
psql -U postgres -d contract_refund_system -c "SELECT 1;"
```

### Module Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Tests Failing

```bash
# Run with verbose output
pytest -vv

# Run single test for debugging
pytest tests/test_main.py::test_health_check -vv
```

## Documentation

- **Database**: See `database/README.md` and `database/docs/`
- **API**: See Swagger docs at `/docs` when running
- **PRD**: See `artifacts/product-docs/PRD.md`
- **Implementation Plan**: See `artifacts/product-docs/backend-implementation-plan.md`

## Support

For issues or questions:
1. Check existing documentation
2. Review PRD and implementation plan
3. Contact development team

---

**Version**: 1.0.0
**Last Updated**: 2025-11-09
