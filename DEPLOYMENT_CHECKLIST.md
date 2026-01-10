# 🚀 Deployment Checklist для Railway

## ✅ Что готово:

### 1. **Docker + ffmpeg** ✅
- `Dockerfile` содержит `ffmpeg` для нарезки кадров
- Все зависимости установлены

### 2. **Redis + Background Worker** ✅
- `worker.py` - RQ worker для фоновых задач
- `Procfile` - запускает `web` + `worker`
- Фоновый анализ через Redis Queue

### 3. **Lazy Analysis Strategy** ✅
**Клиентские креативы:**
- Анализируются ТОЛЬКО после 5 конверсий
- Экономия: 90% API costs

**Benchmark креативы (FB Ad Library):**
- Анализируются СРАЗУ (is_benchmark=True)
- Автозапуск при старте API

### 4. **Market Winners Integration** ✅
- Каждый winner → PatternPerformance
- Thompson Sampling подхватывает "золотые гены"
- Клиенты видят winning patterns во вкладке Trends

### 5. **Cost Tracking** ✅
- Каждый анализ = $0.15
- Логирование затрат в `analysis_cost_cents`
- Endpoint для просмотра total costs

---

## 📋 Railway Deployment Steps:

### Шаг 1: Добавь Redis
```
Railway Dashboard → Add Service → Redis
```
Railway автоматически свяжет с backend через `REDIS_URL`

### Шаг 2: Environment Variables
```bash
# AI
ANTHROPIC_API_KEY=sk-ant-xxx

# Storage
STORAGE_TYPE=r2
R2_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=creative-optimizer-videos

# Attribution
RUDDERSTACK_WRITE_KEY=xxx
RUDDERSTACK_WEBHOOK_SECRET=xxx

# Influencers
MODASH_API_KEY=xxx

# Database (auto-set by Railway)
DATABASE_URL=postgresql://...

# Redis (auto-set by Railway)
REDIS_URL=redis://...
```

### Шаг 3: Deploy
```bash
git add .
git commit -m "Production ready: Lazy analysis + benchmarks"
git push

# Railway auto-deploys from GitHub
```

### Шаг 4: Verify Deployment
После деплоя проверь логи:

**Ожидаемые логи:**
```
🚀 Starting TG Reposter API...
✅ Database initialized
🌱 Seeding database with market benchmarks...
  ✅ problem_agitation + frustration → 14.5% CVR
  ...
✅ Seeded 10 market benchmark patterns!

🌱 Seeding benchmark videos from Facebook Ad Library...
  ✅ Duolingo - 'Too Busy to Learn?' Winner → 14.5% CVR
  ✅ Peloton - Before/After Transformation → 13.2% CVR
  ...
✅ Seeded 5 benchmark videos!

🎯 Triggering analysis for benchmark: Duolingo - 'Too Busy to Learn?' Winner
🔄 Triggering deep analysis for: Duolingo - 'Too Busy to Learn?' Winner
✅ Analysis job enqueued: job-123

✅ Redis connected
✅ Task queue connected
✅ API started successfully
```

**RQ Worker logs (отдельный процесс):**
```
🚀 Starting RQ Worker...
✅ Worker listening on 'default' queue

🎬 Starting deep analysis for creative: uuid-123
📹 Analyzing video: https://example.com/duolingo-winner.mp4
✅ Extracted 3 frames
✅ Claude analyzed: problem_agitation + frustration
💰 COST TRACKING: Duolingo analysis cost $0.15 (~15 cents)
✅ WINNER DECONSTRUCTED: Duolingo → problem_agitation + frustration (CVR: 14.5%)
🏆 MARKET WINNER ADDED: problem_agitation + frustration → 14.5% CVR (n=1)
```

---

## 🧪 Test После Деплоя:

### 1. Health Check
```bash
curl https://your-app.railway.app/health
# Expect: {"status":"healthy", ...}
```

### 2. Check Benchmarks
```bash
curl https://your-app.railway.app/api/v1/creative/list
# Expect: 5 benchmark videos with is_benchmark=true
```

### 3. Check Market Winners
```bash
curl https://your-app.railway.app/api/v1/rudderstack/thompson-sampling?product_category=fitness
# Expect: Recommendations based on seeded patterns
```

### 4. Upload Test Creative
```bash
# Upload через админку
# После 5 конверсий → автоматически запустится Claude Vision!
```

---

## 💰 Cost Estimate (Production):

**Railway Starter ($5/mo):**
- Backend API (1 container)
- PostgreSQL (512MB)
- Redis (256MB)

**Cloudflare R2 (Free tier):**
- 10 GB storage
- 1M reads/month

**Anthropic Claude Vision:**
- $0.15 per creative analysis
- ~5 winners/month = $0.75
- **Total AI cost: <$1/mo** 🎯

**Total: $6/month for MVP** ✅

---

## 🎯 After Deployment - First Steps:

1. ✅ Verify benchmarks loaded (5 videos)
2. ✅ Check RQ worker is processing analysis jobs
3. ✅ Open admin: `https://your-app.railway.app/dashboard`
4. ✅ Navigate to "Patterns" tab → See seeded benchmarks
5. ✅ Upload first client creative
6. ✅ Simulate 5 conversions → Watch auto-analysis trigger!

---

## 🐛 Troubleshooting:

### Worker not processing jobs
**Check:**
```bash
# Railway logs for worker process
# Ensure REDIS_URL is set
```

### Claude Vision fails
**Check:**
```bash
# Ensure ANTHROPIC_API_KEY is valid
# Check ffmpeg is installed: docker exec -it <container> ffmpeg -version
```

### Benchmarks not seeded
**Check:**
```bash
# Railway logs: Look for "Seeding benchmark videos"
# If missing, run manually: docker exec -it <container> python scripts/seed_benchmark_videos.py
```

---

**Ready to launch! 🚀**
