# 🚀 Quick Start - Local Development

Run Creative Optimizer locally in 5 minutes (no payment needed!)

## Prerequisites

- Docker Desktop installed
- Git (to clone repo - already done)
- Python 3.11+ (optional - for testing without Docker)

## Option 1: Docker Compose (Recommended - Full Stack)

### Step 1: Setup Environment

```bash
cd ~/creative-optimizer

# Copy environment file
cp .env.example .env

# Edit .env and set minimum required variables
nano .env
```

**Minimum .env configuration:**
```bash
# Database (automatically set by docker-compose)
DATABASE_URL=postgresql://utm_user:utm_password@postgres:5432/utm_tracking
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=local-dev-secret-change-in-production

# Product settings
PRODUCT_THEME=white
ATTRIBUTION_WINDOW_HOURS=72
USE_PUBLIC_DATA_BOOTSTRAP=true
STORAGE_TYPE=local
```

### Step 2: Start Services

```bash
# Start all services (API, PostgreSQL, Redis, Grafana, Prometheus)
docker-compose up -d

# Check logs
docker-compose logs -f api

# Wait for "Application startup complete"
```

### Step 3: Access Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana** (monitoring): http://localhost:3000 (admin/admin)
- **Prometheus** (metrics): http://localhost:9090

### Step 4: Create Admin User

```bash
# Via API docs (http://localhost:8000/docs)
# Or via curl:

curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "test123"
  }'
```

### Step 5: Get JWT Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "test123"
  }'

# Copy the "access_token" from response
```

### Step 6: Test Features!

**1. Test Public Data Bootstrap:**
```bash
curl http://localhost:8000/api/v1/bootstrap/fitness
```

**2. Test Pattern Gap Finder:**
```bash
# Via http://localhost:8000/docs
# Navigate to /api/v1/patterns/gaps
# Execute with category=fitness
```

**3. Test Video Analysis (local file):**
```python
# If you have a video file
from utils.video_analyzer import analyze_video_quick

result = analyze_video_quick("path/to/video.mp4")
print(result)
```

---

## Option 2: Python Only (Faster for dev, no monitoring)

### Step 1: Install Dependencies

```bash
cd ~/creative-optimizer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup PostgreSQL & Redis

**Mac (via Homebrew):**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis

# Create database
createdb utm_tracking
```

**Or use Docker for DB only:**
```bash
docker run -d --name postgres \
  -e POSTGRES_DB=utm_tracking \
  -e POSTGRES_USER=utm_user \
  -e POSTGRES_PASSWORD=utm_password \
  -p 5432:5432 \
  postgres:15-alpine

docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Step 3: Run API

```bash
# Setup .env
cp .env.example .env
nano .env  # Set DATABASE_URL, etc

# Run migrations
alembic upgrade head

# Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access: http://localhost:8000/docs

---

## Testing the Full Workflow

### Test 1: Public Data Analysis

```bash
# Get TikTok Creative Center data (simulated)
curl http://localhost:8000/api/v1/scrapers/tiktok?category=fitness&limit=20

# Result: List of ads with stability scores
```

### Test 2: Pattern Stability Classification

```python
from utils.trend_classifier import TrendClassifier
from utils.scrapers.tiktok_creative_center import scrape_tiktok_top_ads

# Get public data
ads = scrape_tiktok_top_ads(category="fitness", limit=100)

# Find stable patterns
stable_ads = [ad for ad in ads if ad["stability_score"] > 0.6]

print(f"Found {len(stable_ads)} stable patterns out of {len(ads)}")
# → "Found 35 stable patterns out of 100"
```

### Test 3: Pattern Gap Finder

```python
from utils.public_data_bootstrap import PublicDataBootstrap

bootstrap = PublicDataBootstrap(category="fitness")
bootstrap.load_public_data()

# Find untested combinations
gaps = bootstrap.find_untested_gaps()

for gap in gaps[:5]:
    print(f"Gap: {gap['hook']} + {gap['emotion']} (score: {gap['gap_score']})")

# → "Gap: transformation + curiosity (score: 0.88)"
```

### Test 4: Video Analysis

```python
from utils.video_analyzer import analyze_video_quick

# Analyze a local video
result = analyze_video_quick("test_video.mp4")

print(f"Pacing: {result['pacing']}")
print(f"Has face: {result['has_face']}")
print(f"Audio energy: {result['audio_energy']}")
print(f"Scenes: {result['num_scenes']}")
```

### Test 5: Early Signals (24h analysis)

```python
from utils.early_signals import EarlySignalsAnalyzer

analyzer = EarlySignalsAnalyzer()

verdict = analyzer.analyze_24h_performance(
    impressions=5000,
    clicks=150,  # CTR: 3%
    landing_views=120,
    landing_bounces=40,
    avg_time_on_page=6.5
)

print(f"Signal: {verdict['signal']}")
print(f"Recommendation: {verdict['recommendation']}")
print(f"Predicted CVR: {verdict['predicted_final_cvr']}")

# → "Signal: strong_positive"
# → "Recommendation: SCALE"
# → "Predicted CVR: 0.12"
```

---

## Stopping Services

```bash
# Stop Docker Compose
docker-compose down

# Or stop but keep data
docker-compose stop
```

---

## Useful Commands

```bash
# View logs
docker-compose logs -f api

# Restart a service
docker-compose restart api

# Access database
docker-compose exec postgres psql -U utm_user utm_tracking

# Access Redis
docker-compose exec redis redis-cli

# Run migrations
docker-compose exec api alembic upgrade head
```

---

## Next Steps

1. ✅ Test all features locally
2. ✅ Verify scrapers work
3. ✅ Test video analysis with real files
4. ✅ Create sample data
5. 💳 When ready → Deploy to Railway ($5/month)

---

## Troubleshooting

### Port already in use

```bash
# Find what's using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)
```

### Database connection error

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres
```

### OpenCV/librosa errors

```bash
# Mac
brew install ffmpeg

# The Docker image already has all dependencies
```

---

**Ready to test locally? Run `docker-compose up -d` and go! 🚀**
