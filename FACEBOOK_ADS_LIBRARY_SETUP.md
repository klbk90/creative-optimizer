# 🔥 Facebook Ads Library Integration - Setup Guide

**Цель:** Загрузить РЕАЛЬНЫЕ успешные креативы из Facebook Ads Library и автоматически проанализировать их через Claude Vision.

---

## 📋 Что это дает?

Вместо ФЕЙКОВЫХ seed данных (`seed_benchmarks.py`), система будет:

1. **Парсить Facebook Ads Library** → находить успешные EdTech/Fitness/etc. креативы
2. **Оценивать CVR** → по времени показа рекламы (30+ дней = успешная)
3. **Скачивать видео** (опционально)
4. **Анализировать через Claude Vision** → извлекать hook_type, emotion, pacing
5. **Сохранять в базу** → с Bayesian Prior (α, β)

---

## 🔑 Шаг 1: Получить Facebook Access Token

### Вариант A: Быстрый (для тестирования, токен на 1-2 часа)

1. Перейти на https://developers.facebook.com/tools/accesstoken/
2. Нажать **"Get User Access Token"**
3. Выбрать разрешения:
   - `ads_read` (обязательно!)
   - `pages_read_engagement`
4. Скопировать токен

### Вариант B: Долгосрочный (для production)

1. Создать Facebook App:
   - Перейти на https://developers.facebook.com/apps/
   - **Create App** → **Business** → Название: "Creative Optimizer"

2. Добавить **Marketing API**:
   - В левом меню: **Add Product** → **Marketing API**

3. Получить токен:
   - **Tools** → **Access Token Tool**
   - Выбрать свое приложение
   - Нажать **Generate Token**
   - Выбрать permissions: `ads_read`, `pages_read_engagement`

4. Продлить токен (60 дней):
   ```bash
   curl "https://graph.facebook.com/v18.0/oauth/access_token?\
     grant_type=fb_exchange_token&\
     client_id=YOUR_APP_ID&\
     client_secret=YOUR_APP_SECRET&\
     fb_exchange_token=SHORT_LIVED_TOKEN"
   ```

---

## 🔧 Шаг 2: Настроить Environment Variables

Добавьте в `.env`:

```bash
# Facebook Ads Library API
FACEBOOK_ACCESS_TOKEN=your_long_token_here
FACEBOOK_APP_ID=your_app_id

# Claude Vision API (уже должен быть)
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🚀 Шаг 3: Запустить импорт

### Вариант 1: Через API (рекомендуется)

```bash
# Проверить статус
curl http://localhost:8000/api/v1/market/status | jq

# Очистить seed данные (фейковые паттерны)
curl -X DELETE http://localhost:8000/api/v1/market/clear-seed-data | jq

# Импортировать РЕАЛЬНЫЕ креативы из Facebook
curl -X POST http://localhost:8000/api/v1/market/import/facebook-ads/sync \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": "language learning app",
    "ad_reached_countries": "US",
    "limit": 5,
    "analyze_with_claude": false
  }' | jq
```

### Вариант 2: Через Python скрипт

```bash
docker exec utm-api python3 scripts/facebook_ads_parser.py
```

---

## 📊 Что будет импортировано?

### Пример найденных креативов:

```json
{
  "total_found": 5,
  "successfully_ingested": 5,
  "creatives": [
    {
      "name": "FB Ad: Duolingo - a3f7e8d2",
      "market_cvr": 0.04,
      "market_longevity_days": 45,
      "bayesian_prior": {
        "alpha": 1800,
        "beta": 43200
      },
      "source_platform": "facebook_ad_library",
      "is_public": true
    }
  ]
}
```

### Как оценивается CVR?

Facebook НЕ публикует точный CVR, поэтому мы оцениваем по эвристикам:

| Longevity (дни) | Estimated CVR | Логика |
|-----------------|---------------|--------|
| 30+ дней | **4.0%** | Долгие кампании = успешные |
| 14-30 дней | **2.5%** | Средние кампании |
| <14 дней | **1.5%** | Короткие кампании |

Для более точной оценки нужен **Facebook Marketing API** (требует Business Verification).

---

## 🎯 Ручной анализ видео (если у вас есть свои)

Если у вас есть **собственные успешные видео**, загрузите их через `ingest_market_data.py`:

```python
from scripts.ingest_market_data import ingest_benchmark_video

result = ingest_benchmark_video(
    video_url="https://your-server.com/videos/winner.mp4",  # или локальный путь
    creative_name="My Winning Creative",
    product_category="language_learning",
    market_cvr=0.06,  # Ваш РЕАЛЬНЫЙ CVR (6%)
    market_longevity_days=60,  # Сколько дней показывали
    source_platform="manual_upload",
    avg_daily_clicks=2000,  # Средний трафик в день

    # Опционально (если известно):
    hook_type="problem_agitation",
    emotion="frustration",
    pacing="fast",
    target_audience_pain="no_time"
)
```

Это создаст **Bayesian Prior**: α=7200, β=112800 (60 дней × 2000 кликов/день × 6% CVR)

---

## 🤖 Claude Vision анализ (автоматический)

Если у вас есть **реальные видео файлы**, система может:

1. Скачать видео из Facebook (через video_url)
2. Извлечь 3 кадра: **0s (Hook), 3s (Body), 10s (CTA)**
3. Отправить в **Claude Vision API**
4. Получить автоматические теги:
   - `hook_type`: problem_agitation, question, social_proof...
   - `emotion`: frustration, curiosity, trust...
   - `pacing`: fast, medium, slow
   - `target_audience_pain`: no_time, skepticism...

**Включить Claude Vision:**

```bash
curl -X POST http://localhost:8000/api/v1/market/import/facebook-ads/sync \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": "EdTech learning",
    "limit": 3,
    "analyze_with_claude": true  # ← ВКЛЮЧИТЬ
  }' | jq
```

**Стоимость:** ~$0.15 за видео (3 кадра × Claude Vision API)

---

## 🎨 На какую аудиторию собирать данные?

Это зависит от вашего клиента! Выберите категорию:

### EdTech (Language Learning)
```bash
search_terms="language learning app"
product_category="language_learning"
```

### Fitness / Health
```bash
search_terms="fitness workout app"
product_category="fitness"
```

### Programming / Career
```bash
search_terms="coding bootcamp online"
product_category="programming"
```

### Finance / Investing
```bash
search_terms="investing app crypto"
product_category="finance"
```

---

## 📂 Куда сохраняются данные?

### 1. `creatives` таблица:
```sql
SELECT name, market_cvr, market_longevity_days, is_public, is_benchmark
FROM creatives
WHERE is_benchmark = true;
```

### 2. `pattern_performance` таблица:
```sql
SELECT hook_type, emotion, avg_cvr, bayesian_alpha, bayesian_beta, source, weight
FROM pattern_performance
WHERE source = 'benchmark';
```

**Ключевое отличие от seed данных:**
- `source = 'benchmark'` (вместо 'client')
- `weight = 2.0` (приоритет в Thompson Sampling)
- `is_public = true` (доступны всем клиентам)

---

## ✅ Проверка результатов

### 1. API статус:
```bash
curl http://localhost:8000/api/v1/market/status | jq
```

### 2. Thompson Sampling:
```bash
curl 'http://localhost:8000/api/v1/rudderstack/thompson-sampling?product_category=language_learning' | jq
```

### 3. Frontend:
- **http://localhost:3001/patterns** → Pattern Discovery
- **http://localhost:3001/trends** → Market Trends

---

## 🚨 Troubleshooting

### Ошибка: "Invalid OAuth access token"
→ Токен истек. Получите новый через https://developers.facebook.com/tools/accesstoken/

### Ошибка: "No ads found"
→ Попробуйте другие search_terms:
```bash
"online course"
"learn English app"
"workout fitness"
```

### Mock Mode (⚠️ FACEBOOK_ACCESS_TOKEN not set)
→ Система работает с ДЕМО данными. Для реальных данных установите токен.

---

## 📝 Roadmap

- [x] Facebook Ads Library API integration
- [x] Bayesian Prior calculation
- [x] Claude Vision auto-analysis
- [ ] TikTok Ads Library integration
- [ ] YouTube Ads integration
- [ ] Google Ads Library

---

## 💡 Рекомендации

1. **Начните с малого:** Импортируйте 3-5 креативов для тестирования
2. **Используйте свои видео:** Если у вас есть успешные кампании, загрузите их вручную с РЕАЛЬНЫМ CVR
3. **Включайте Claude Vision:** Только для креативов которые вы планируете использовать как эталон
4. **Очистите seed данные:** Перед production запуском удалите фейковые паттерны

**Готово! Система теперь может импортировать РЕАЛЬНЫЕ market benchmarks из Facebook Ads Library! 🚀**
