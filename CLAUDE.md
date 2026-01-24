# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

### Backend (Python/FastAPI)
```bash
make install          # pip install -r requirements.txt
make dev              # uvicorn api.main:app --reload (port 8000)
make migrate          # alembic upgrade head
make test             # pytest tests/
make prod             # docker-compose up -d
```

### Frontend (React/Vite)
```bash
cd frontend
npm install
npm run dev           # Vite dev server (port 5173)
npm run build         # Production build to dist/
```

### Running Single Tests
```bash
pytest tests/unit/test_file.py::test_function -v
pytest -m unit        # Run only unit tests
pytest -m integration # Run only integration tests
pytest -m ml          # Run ML-specific tests
```

### Code Quality
```bash
black .               # Format Python code
flake8                # Lint Python code
isort .               # Sort imports
mypy .                # Type checking
```

## Architecture Overview

This is a full-stack SaaS platform for mobile app marketers to optimize video ad creatives using ML predictions.

### Tech Stack
- **Backend**: FastAPI + PostgreSQL + Redis + Alembic migrations
- **Frontend**: React 18 + Vite + Tailwind CSS + Recharts
- **ML**: scikit-learn (KMeans, PCA), LightGBM, Thompson Sampling, Markov Chains
- **Video Analysis**: OpenCV, librosa (audio), MoviePy
- **Deployment**: Docker Compose, Railway (backend), Vercel (frontend)

### Key Directories
```
api/
  main.py              # FastAPI app entry, route registration
  routers/             # API endpoints (auth, analytics, creative_ml, etc.)
  dependencies.py      # Auth utilities, dependency injection

database/
  models.py            # SQLAlchemy ORM models (18 tables)
  schemas.py           # Pydantic request/response schemas
  base.py              # DB engine and session management

utils/
  markov_chain.py      # Creative pattern prediction
  thompson_sampling.py # Exploration/exploitation for testing
  creative_analyzer.py # Video content analysis
  gradient_boosting_predictor.py  # LightGBM CVR model
  storage.py           # S3/R2/Spaces abstraction

frontend/src/
  pages/               # Route components (Dashboard, CreativeLab, etc.)
  components/          # Reusable UI (Layout, ProtectedRoute)
  contexts/            # Auth context provider
  services/api.js      # Axios API client
```

### API Structure
Routers are organized by domain:
- `auth.py` - JWT authentication
- `creative_ml.py` - ML model predictions (Markov Chain + Thompson Sampling)
- `analytics.py` - Conversion funnel analysis
- `pattern_optimization.py` - Gap finder, uniqueness scoring
- `influencer_search.py` - Influencer discovery via Modash API
- `market_intelligence.py` - Facebook Ads Library import

### Database
- PostgreSQL with SQLAlchemy ORM
- Alembic for migrations (`alembic/versions/`)
- Multi-tenant design: all content tables have `user_id` foreign key
- Key models: User, Creative, Conversion, UTMLink, TikTokVideo, Pattern

### ML Pipeline
1. **Video Analysis**: Extract features via OpenCV (scenes, colors, motion) + librosa (audio energy)
2. **Pattern Extraction**: Identify hooks, emotions, pacing from creatives
3. **Clustering**: KMeans groups similar creatives
4. **Prediction**: Markov Chain for pattern sequences, LightGBM for CVR
5. **Optimization**: Thompson Sampling balances exploration vs exploitation
6. **Learning**: RudderStack webhooks update model with conversion data

### Authentication
- JWT tokens with bcrypt password hashing
- Protected routes require `Authorization: Bearer <token>` header
- Frontend uses React Context for auth state

## Environment Variables

Key variables in `.env` (see `.env.example`):
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `JWT_SECRET_KEY` - Token signing key
- `STORAGE_TYPE` - local/r2/spaces/s3 for video storage
- `ANTHROPIC_API_KEY` - For Claude API integration

## Docker Services

```bash
docker-compose up -d  # Start all services
```
- `postgres` (5433) - Database
- `redis` (6380) - Cache/Queue
- `api` (8000) - FastAPI backend
- `frontend` (3001) - React UI via nginx
- `admin-bot` - Telegram bot worker
