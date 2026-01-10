# 🚂 Railway Deployment Guide

**Время деплоя: 10 минут**

## ✅ Что готово:

1. **Dockerfile** - Railway-ready
2. **railway.json** - автоконфиг
3. **storage.py** - Cloudflare R2 интеграция  
4. **seed_benchmarks.py** - 10 winning patterns из Facebook Ad Library
5. **Автозапуск seed** - при старте API

## 🚀 Quick Start:

```bash
# 1. Push to GitHub
git add .
git commit -m "Railway ready"
git push

# 2. Railway.app → New Project → Deploy from GitHub
# 3. Add PostgreSQL database
# 4. Set environment variables (см. ниже)
# 5. Deploy автоматически!
```

## 🔧 Environment Variables:

```bash
# Required
JWT_SECRET_KEY=your-secret-key
STORAGE_TYPE=r2
R2_ENDPOINT_URL=https://YOUR_ACCOUNT.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=creative-optimizer-videos

# Optional
MODASH_API_KEY=xxx
OPENAI_API_KEY=xxx
```

## 🎯 После деплоя:

Клиент сразу увидит:
- ✅ 10 market benchmarks (14.5% CVR top pattern!)
- ✅ Thompson Sampling рекомендации
- ✅ AI Score для инфлюенсеров
- ✅ Pattern Discovery с Bayesian stats

**Public URL:** `https://your-app.railway.app`

**Стоимость:** $5-10/месяц

Done! 🎉
