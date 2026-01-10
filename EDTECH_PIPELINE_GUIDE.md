# AI-Driven Creative Optimizer для EdTech

## 🎯 Бизнес-цель

**Снизить стоимость привлечения клиента (CAC)** за счет быстрого и дешевого тестирования паттернов креативов на микро-инфлюенсерах с последующим масштабированием "чемпионов".

---

## 📊 Архитектура системы

### Основной флоу (The Loop)

```
1. INGESTION
   └─> Загрузка видео-креативов

2. DISCOVERY
   └─> Поиск 50-100 микро-инфлюенсеров (Modash API)
       - 5K–50K подписчиков
       - Engagement Rate > 3%
       - Ниша: EdTech (IT, Дизайн, Языки)

3. TESTING (Песочница)
   └─> Раздача уникальных UTM-ссылок
       - Каждый инфлюенсер получает utm_id
       - Малый бюджет ($50-100 per influencer)

4. TRACKING
   └─> RudderStack ловит события:
       - Page Viewed → Сохранение UTM сессии
       - Order Completed → Атрибуция конверсии

5. ANALYSIS (Post-hoc)
   └─> Для успешных креативов запускаем "вскрытие":
       - OpenCV/Librosa: темп, звук, лица
       - Claude Vision: психологические хуки, эмоции, боли

6. LEARNING
   └─> Bayesian обновление (Beta-распределение)
       - P(conversion | pattern) → pattern_performance
       - Thompson Sampling для выбора следующих паттернов

7. SCALE
   └─> Вердикт: какие паттерны масштабировать в FB/TikTok
```

---

## 🛠 Технический стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Python + FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Data Pipeline | RudderStack (server-side SDK) |
| Influencer API | Modash |
| ML/Stats | scipy.stats (Beta distribution), Thompson Sampling |
| AI Vision | Claude 3.5 Sonnet (Anthropic) |
| Migrations | Alembic |

---

## 🗄 Схема базы данных

### Ключевые таблицы

#### 1. `users`
Пользователи SaaS платформы (multi-tenancy).

#### 2. `creatives`
Видео-креативы с метаданными и паттернами.

**EdTech-специфичные поля:**
- `target_audience_pain`: Боль ЦА (no_time, too_expensive, fear_failure, etc.)
- `hook_type`: Тип хука (question, wait, bold_claim, etc.)
- `emotion`: Эмоция (curiosity, excitement, fear, etc.)
- `pacing`: Темп (fast, medium, slow)
- `cta_type`: Call-to-action (urgency, direct, soft, etc.)

#### 3. `traffic_sources`
UTM tracking для трафика от инфлюенсеров.

**Новые поля (v2.0):**
- `creative_id`: Связь с креативом
- `influencer_handle`: Username инфлюенсера
- `influencer_email`: Email для outreach
- `influencer_followers`: Количество подписчиков
- `influencer_engagement_rate`: ER * 10000
- `influencer_status`: potential, contacted, agreed, posted, rejected
- `external_id`: RudderStack anonymousId

#### 4. `conversions`
Конверсии (покупки, подписки).

**Новые поля:**
- `external_id`: RudderStack anonymousId для точной атрибуции

#### 5. `pattern_performance`
Агрегированная производительность паттернов (для Markov Chain).

**Новые поля:**
- `pattern_hash`: Быстрый поиск по комбинации паттернов
- `target_audience_pain`: EdTech-специфичная боль ЦА
- `avg_cvr`: Средний CVR * 10000 (Bayesian estimate)
- `confidence_interval_lower/upper`: 95% доверительный интервал

#### 6. `user_sessions`
Сессии пользователей для автоатрибуции.

---

## 📦 Основные модули

### 1. `database/models.py`
SQLAlchemy модели для PostgreSQL.

### 2. `api/routers/rudderstack.py`
**Webhook для RudderStack:**
- `POST /api/v1/rudderstack/track` - обработка событий
- `GET /api/v1/rudderstack/thompson-sampling` - рекомендации паттернов

**Ключевые функции:**
- `handle_page_view()` - сохранение UTM сессии
- `handle_order_completed()` - автоатрибуция + Bayesian update
- `bayesian_update_cvr()` - обновление CVR с Beta-распределением
- `thompson_sampling()` - выбор лучших паттернов для тестирования

### 3. `utils/modash_client.py`
**Modash API клиент:**
```python
from utils.modash_client import ModashClient

client = ModashClient(api_key="your_key")

# Поиск микро-инфлюенсеров
influencers = client.search_edtech_influencers(
    niche="programming",
    geo=["US", "GB", "CA"],
    min_followers=5000,
    max_followers=50000,
    min_engagement=0.03,
    limit=50
)
```

### 4. `utils/influencer_finder.py`
**Поиск инфлюенсеров + создание traffic sources:**
```python
from utils.influencer_finder import find_and_assign_influencers

results = find_and_assign_influencers(
    creative_id="uuid",
    campaign_tag="edtech_jan_2026",
    niche="programming",
    target_audience_pain="no_time",
    n_influencers=20,
    db=db
)

# Результат:
# - influencers: найденные инфлюенсеры
# - traffic_sources: созданные UTM ссылки
# - outreach_drafts: готовые письма для отправки
```

### 5. `utils/creative_analyzer.py`
**Claude Vision API для анализа креативов:**
```python
from utils.creative_analyzer import CreativeAnalyzer

analyzer = CreativeAnalyzer()

analysis = analyzer.analyze_video(
    video_path="creative.mp4",
    frames_to_analyze=[0, 2, 5, 8]
)

# Результат:
# {
#   "hook_type": "question",
#   "emotion": "curiosity",
#   "pacing": "fast",
#   "cta_type": "urgency",
#   "features": {...},
#   "confidence": 0.85
# }
```

### 6. `utils/markov_chain.py`
**Markov Chain для предсказания CVR:**
```python
from utils.markov_chain import MarkovChainPredictor

predictor = MarkovChainPredictor(
    db=db,
    user_id="uuid",
    product_category="language_learning"
)

prediction = predictor.predict_cvr(
    hook_type="question",
    emotion="curiosity",
    pacing="fast",
    cta_type="urgency"
)

# Результат:
# {
#   "predicted_cvr": 0.125,  # 12.5%
#   "confidence_score": 0.85,
#   "confidence_interval": (0.08, 0.17),
#   "prediction_method": "exact_match"
# }
```

---

## 🚀 Quick Start

### 1. Установка зависимостей

```bash
cd /Users/aliakseiramanchyk/creative-optimizer

# Установить Python пакеты
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env
```

### 2. Настройка .env

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/creative_optimizer

# APIs
ANTHROPIC_API_KEY=your_anthropic_key
MODASH_API_KEY=your_modash_key
RUDDERSTACK_WRITE_KEY=your_rudderstack_key

# RudderStack
RUDDERSTACK_DATA_PLANE_URL=https://your-instance.dataplane.rudderstack.com
```

### 3. Запуск миграций

```bash
# Применить миграции
alembic upgrade head

# Если нужно откатить
alembic downgrade -1
```

### 4. Запуск API

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Запуск теста

```bash
python test_edtech_pipeline.py
```

---

## 📈 Примеры использования

### Сценарий 1: Тестирование нового креатива

```python
from database.base import SessionLocal
from database.models import Creative
from utils.influencer_finder import find_and_assign_influencers
import uuid

db = SessionLocal()

# 1. Создать креатив
creative = Creative(
    id=uuid.uuid4(),
    user_id="your-user-id",
    name="Python Course Promo",
    creative_type="ugc",
    product_category="programming",
    target_audience_pain="no_time",  # ⭐ EdTech-специфично
    hook_type="question",
    emotion="curiosity",
    pacing="fast",
    cta_type="urgency",
    status="testing"
)

db.add(creative)
db.commit()

# 2. Найти инфлюенсеров и создать traffic sources
results = find_and_assign_influencers(
    creative_id=str(creative.id),
    campaign_tag="python_jan_2026",
    niche="programming",
    target_audience_pain="no_time",
    n_influencers=20,
    db=db
)

print(f"Найдено инфлюенсеров: {len(results['influencers'])}")
print(f"Создано UTM ссылок: {len(results['traffic_sources'])}")
print(f"Писем к отправке: {len(results['outreach_drafts'])}")

# 3. Отправить письма (manual outreach или через API)
for draft in results['outreach_drafts']:
    print(f"\nTo: {draft['to']}")
    print(f"Subject: {draft['subject']}")
    print(draft['body'])
```

### Сценарий 2: Обработка RudderStack событий

**Webhook конфигурация в RudderStack:**

```json
{
  "webhookUrl": "https://your-domain.com/api/v1/rudderstack/track",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

**Событие: Page Viewed**

```json
POST /api/v1/rudderstack/track

{
  "event": "Page Viewed",
  "userId": "user_123",
  "anonymousId": "anon_456",
  "properties": {
    "utm_id": "inf_edutech_creator_1_abc123"
  },
  "context": {
    "ip": "192.168.1.1",
    "device": {
      "type": "mobile"
    }
  }
}
```

**Событие: Order Completed**

```json
POST /api/v1/rudderstack/track

{
  "event": "Order Completed",
  "userId": "user_123",
  "anonymousId": "anon_456",
  "properties": {
    "order_id": "ord_789",
    "total": 49.00,
    "currency": "USD",
    "product_name": "Python Course"
  }
}
```

**Результат:**
- Автоатрибуция конверсии к `utm_id`
- Обновление `pattern_performance` с Bayesian методом
- Пересчет CVR с доверительным интервалом

### Сценарий 3: Thompson Sampling рекомендации

```bash
# Получить топ-5 паттернов для тестирования
curl "http://localhost:8000/api/v1/rudderstack/thompson-sampling?product_category=language_learning&n_recommendations=5"
```

**Ответ:**

```json
{
  "product_category": "language_learning",
  "n_patterns_evaluated": 15,
  "recommendations": [
    {
      "pattern_hash": "hook:question|emo:curiosity|pace:fast|pain:no_time|cta:urgency",
      "hook_type": "question",
      "emotion": "curiosity",
      "thompson_score": 0.158,
      "mean_cvr": 0.145,
      "alpha": 16,
      "beta": 94,
      "sample_size": 10,
      "reasoning": "High confidence winner (n=10)"
    },
    ...
  ]
}
```

---

## 🔬 Байесовское обновление (Technical Deep Dive)

### Почему Beta-распределение?

**Beta-распределение** идеально для моделирования conversion rate, потому что:

1. **Диапазон [0, 1]** - идеально для вероятностей
2. **Conjugate prior** - легко обновлять с новыми данными
3. **Интерпретируемые параметры:**
   - `alpha = успехи + 1`
   - `beta = неудачи + 1`

### Формула обновления

```python
# Prior
alpha_prior = 1.0  # Uniform prior
beta_prior = 1.0

# Likelihood (данные)
total_conversions = 15
total_clicks = 100

# Posterior
alpha = alpha_prior + total_conversions  # 16
beta = beta_prior + (total_clicks - total_conversions)  # 86

# Expected CVR
mean_cvr = alpha / (alpha + beta)  # 15.7%

# 95% Credible Interval
from scipy.stats import beta as beta_dist
lower = beta_dist.ppf(0.025, alpha, beta)  # 9.8%
upper = beta_dist.ppf(0.975, alpha, beta)  # 23.4%
```

### Thompson Sampling

**Идея:** Сэмплируем из Beta-распределения каждого паттерна, выбираем топ-N.

**Баланс Exploration vs Exploitation:**
- Паттерны с высоким CVR и большой выборкой → стабильно высокий sample (exploit)
- Паттерны с малой выборкой → высокая вариативность sample (explore)

```python
import random

for pattern in patterns:
    alpha = 1.0 + pattern.total_conversions
    beta = 1.0 + (pattern.total_clicks - pattern.total_conversions)

    # Сэмплируем из Beta(alpha, beta)
    thompson_score = random.betavariate(alpha, beta)

# Сортируем по thompson_score (выше = лучше)
# Возвращаем top-N
```

---

## 🎓 EdTech Pain Points

### Основные боли ЦА

| Pain Point | Описание | Пример хука |
|------------|----------|-------------|
| `no_time` | Нет времени учиться | "Learn Python in 15 min/day" |
| `too_expensive` | Дорогие курсы | "$5/month instead of $500" |
| `fear_failure` | Страх провала | "95% students get jobs" |
| `no_progress` | Нет прогресса | "See results in 7 days" |
| `need_career_switch` | Смена карьеры | "From teacher to developer in 6 months" |
| `imposter_syndrome` | Синдром самозванца | "No coding experience? Start here" |
| `info_overload` | Перегрузка информацией | "Only what you need to get hired" |

### Использование в системе

```python
# При создании креатива
creative.target_audience_pain = "no_time"

# Pattern performance учитывает pain point
pattern_hash = f"hook:{hook}|emo:{emotion}|pain:{pain}|..."

# Фильтрация рекомендаций
recommendations = thompson_sampling(patterns, pain_point="no_time")
```

---

## 📊 Метрики успеха

### Key Performance Indicators (KPIs)

1. **CAC Reduction** - главная метрика
   - Цель: снизить на 30-50% vs традиционный A/B тест

2. **Pattern Discovery Speed**
   - Цель: найти winning pattern за <$500 spend

3. **Prediction Accuracy**
   - MAE (Mean Absolute Error) < 3%
   - Hit rate (правильных предсказаний) > 75%

4. **Thompson Sampling Efficiency**
   - Regret (упущенная выгода) < 15% vs Oracle

---

## 🔐 Security & Privacy

### Хранение данных

- **Influencer emails:** Зашифрованы в production (AES-256)
- **Customer PII:** Минимизация, хранение только `customer_id` (hash)
- **RudderStack anonymousId:** Используется для атрибуции без PII

### API Keys

**Никогда не коммитьте API ключи!**

```bash
# .gitignore
.env
.env.local
*.key
```

---

## 🐛 Troubleshooting

### Проблема: Конверсии не атрибутируются

**Причина:** Нет user_session для customer_id

**Решение:**
1. Проверить, что Page Viewed события приходят с `utm_id`
2. Проверить, что `customer_id` совпадает в Page Viewed и Order Completed

### Проблема: Pattern performance не обновляется

**Причина:** Нет `pattern_hash` или `creative_id` в traffic_source

**Решение:**
1. Запустить миграцию: `alembic upgrade head`
2. Проверить, что `creative.target_audience_pain` заполнен

### Проблема: Modash API возвращает 429 (Rate Limit)

**Решение:**
```python
import time

for batch in influencers_batches:
    client.search_influencers(...)
    time.sleep(1)  # Rate limiting
```

---

## 📚 Дополнительные ресурсы

### API документация

- **Modash API:** https://docs.modash.io/
- **RudderStack:** https://www.rudderstack.com/docs/
- **Claude API:** https://docs.anthropic.com/

### Научные статьи

- **Thompson Sampling:** "Analysis of Thompson Sampling for the Multi-armed Bandit Problem" (Agrawal & Goyal, 2012)
- **Beta-Binomial Model:** "Bayesian Data Analysis" (Gelman et al., 2013)

### Полезные инструменты

- **Alembic migrations:** https://alembic.sqlalchemy.org/
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/

---

## 🤝 Contributing

Для улучшений системы:

1. Fork репозиторий
2. Создать feature branch: `git checkout -b feature/new-analysis`
3. Коммит изменений: `git commit -m 'Add new pattern analysis'`
4. Push в branch: `git push origin feature/new-analysis`
5. Открыть Pull Request

---

## 📝 Changelog

### v2.0.0 (2026-01-01)
- ✅ Добавлены поля для micro-influencer tracking
- ✅ Добавлена поддержка EdTech pain points
- ✅ Реализован Bayesian update с Beta-распределением
- ✅ Добавлен Thompson Sampling endpoint
- ✅ Интеграция Modash API
- ✅ Автоатрибуция через RudderStack
- ✅ Claude Vision API для анализа креативов

---

## 📞 Support

Для вопросов и помощи:
- Email: support@creative-optimizer.com
- Telegram: @creative_optimizer_support
- GitHub Issues: https://github.com/your-org/creative-optimizer/issues

---

**Удачи в оптимизации CAC! 🚀**
