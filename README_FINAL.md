# Creative Optimizer MVP - READY TO USE! 🚀

AI-powered creative testing platform with **Markov Chain** predictions and **Thompson Sampling** recommendations.

## ⚡ Quick Start (One Command!)

```bash
./setup-and-start.sh
```

That's it! Everything will be configured and started automatically.

## 🌐 Access

- **Frontend UI**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 🎯 ML Features (Working!)

### 1. Markov Chain CVR Prediction
- Анализирует паттерны: `hook_type + emotion + pacing`
- Предсказывает CVR до запуска креатива
- Confidence растет с количеством тестов

### 2. Thompson Sampling Recommendations
- Баланс **exploitation** (проверенные паттерны) vs **exploration** (новые)
- Priority = CVR × confidence + exploration_bonus
- Чем больше данных, тем точнее рекомендации

### 3. Pattern Learning
- Автообновление при добавлении метрик
- Хранит: `avg_cvr`, `sample_size`, `total_conversions`
- GET `/api/v1/creative/patterns/top` - топ паттерны
- GET `/api/v1/creative/patterns/recommend` - умные рекомендации

## 📝 API Endpoints

```bash
# Upload creative
POST /api/v1/creative/upload
  - video (file)
  - creative_name, product_category, creative_type
  - campaign_tag (для группировки)
  - hook_type, emotion, pacing (опционально)
  → Returns: predicted_cvr, confidence

# List creatives
GET /api/v1/creative/creatives?campaign_tag=test_jan_2025

# Update metrics (triggers Markov Chain update!)
PUT /api/v1/creative/creatives/{id}/metrics
  - impressions, clicks, conversions

# Get ML recommendations (Thompson Sampling)
GET /api/v1/creative/patterns/recommend?product_category=language_learning&n_patterns=5

# Top patterns
GET /api/v1/creative/patterns/top?product_category=language_learning
```

## 🧪 Test

```bash
./test-mvp.sh
```

Создаст тестовый креатив, добавит метрики, покажет рекомендации.

## 🛑 Stop

```bash
docker-compose down
```

## 📊 Logs

```bash
docker-compose logs -f api
docker-compose logs -f frontend
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Frontend (React + Vite + Tailwind)   │
│   http://localhost:3001                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   API (FastAPI + ML)                    │
│   http://localhost:8000                 │
│                                          │
│   Routers:                               │
│   • creative_ml.py (Markov + Thompson)  │
│   • utm.py, analytics.py, auth.py       │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌──────────┐      ┌──────────┐
│PostgreSQL│      │  Redis   │
│  :5433   │      │  :6380   │
└──────────┘      └──────────┘
```

## 📦 What's Included

### ML Models (Working!)
- ✅ Markov Chain (pattern → CVR prediction)
- ✅ Thompson Sampling (smart pattern selection)
- ✅ Online learning (updates with each metric)

### Docker Services
- ✅ PostgreSQL 15 (healthy)
- ✅ Redis 7 (healthy)
- ✅ FastAPI backend (with ML)
- ✅ React frontend (5 pages)

### Frontend Pages
- Dashboard - stats overview
- Upload - upload creatives
- Creatives - list with filters
- Analytics - charts
- Patterns - ML recommendations

## 🎨 Frontend Screenshots

Access http://localhost:3001 to see:
- Real-time creative performance
- CVR predictions
- Thompson Sampling recommendations
- Pattern analytics

## 💡 Example Workflow

```bash
# 1. Start system
./setup-and-start.sh

# 2. Upload creative via API or UI
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video.mp4" \
  -F "creative_name=UGC Test 1" \
  -F "product_category=language_learning" \
  -F "campaign_tag=jan_2025" \
  -F "hook_type=before_after" \
  -F "emotion=achievement"

# 3. Run ads, collect metrics

# 4. Update metrics (Markov Chain updates automatically!)
curl -X PUT http://localhost:8000/api/v1/creative/creatives/{id}/metrics \
  -F "impressions=10000" \
  -F "clicks=500" \
  -F "conversions=75"

# 5. Get ML recommendations for next test
curl http://localhost:8000/api/v1/creative/patterns/recommend?product_category=language_learning&n_patterns=5
```

## 🔧 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **ML**: Custom Markov Chain + Thompson Sampling (no external ML libs needed!)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: React 18, Vite, TailwindCSS, Recharts
- **Deployment**: Docker Compose

## 📝 Notes

- Test user pre-created: `00000000-0000-0000-0000-000000000001`
- Videos stored in `/tmp/utm-videos` (local for MVP)
- CVR stored as integer (× 10000) for precision
- Frontend auto-connects to API via nginx proxy

## 🎯 Production Ready?

**MVP**: ✅ Ready for demo/testing

**For Production**, add:
- [ ] Real authentication (OAuth, JWT)
- [ ] Video storage (S3/R2)
- [ ] OpenCV/librosa video analysis
- [ ] Full pattern_optimization router
- [ ] Database migrations (Alembic)
- [ ] Monitoring (Prometheus/Grafana included but optional)

---

**Built with ML at the core! 🧠**

Markov Chain + Thompson Sampling = Smart Creative Testing
