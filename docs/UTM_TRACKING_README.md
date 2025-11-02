# UTM Tracking & Analytics для TikTok → Telegram → Lootbox воронки

## Обзор

Система трекинга позволяет:
- Генерировать UTM ссылки для TikTok видео
- Отслеживать клики через промежуточную landing page
- Трекать конверсии (покупки лутбоксов)
- Анализировать эффективность кампаний
- Считать ROI по каждому источнику трафика

## Воронка

```
TikTok Video
    ↓ (link in bio/comment)
Landing Page (/api/v1/landing/l/{utm_id})
    ↓ (auto-redirect + tracking)
Telegram Channel
    ↓ (CTA в постах)
Lootbox Purchase
```

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте PostgreSQL базу данных:

```bash
# Создать БД
createdb tg_reposter

# Или через psql
psql -U postgres
CREATE DATABASE tg_reposter;
```

Настройте переменные окружения в `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tg_reposter

# Redis (для кеша и очередей)
REDIS_URL=redis://localhost:6379/0

# JWT для аутентификации
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Landing page настройки
DEFAULT_TELEGRAM_CHANNEL=https://t.me/sportschannel
CHANNEL_NAME=Sports Hub
CHANNEL_DESCRIPTION=Daily sports highlights & discussions
```

### 3. Инициализация БД через Alembic

```bash
# Инициализировать alembic (если еще не сделано)
alembic init alembic

# Создать миграцию
alembic revision --autogenerate -m "Add TikTok tracking models"

# Применить миграцию
alembic upgrade head
```

**Или** создать таблицы напрямую через Python:

```python
from database.base import Base, engine
from database.models import *

# Создать все таблицы
Base.metadata.create_all(bind=engine)
```

### 4. Запуск API

```bash
# Development mode
python api/main.py

# Production mode (с gunicorn)
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

API будет доступно на: `http://localhost:8000`

Документация: `http://localhost:8000/docs`

---

## Использование API

### 1. Генерация UTM ссылки

```bash
curl -X POST "http://localhost:8000/api/v1/utm/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "http://localhost:8000/api/v1/landing/l",
    "source": "tiktok",
    "campaign": "football_jan_2025",
    "content": "video_messi_goal"
  }'
```

Ответ:
```json
{
  "success": true,
  "utm_link": "http://localhost:8000/api/v1/landing/l/tiktok_a7b3c_8f2e1",
  "utm_id": "tiktok_a7b3c_8f2e1"
}
```

**Эту ссылку** нужно вставить в TikTok bio или комментарии!

### 2. Просмотр landing page

Откройте ссылку в браузере:
```
http://localhost:8000/api/v1/landing/l/tiktok_a7b3c_8f2e1
```

Landing page автоматически:
- Отобразит красивую страницу с информацией о канале
- Зарекордит клик в БД
- Через 3 секунды редиректнет на Telegram
- Отправит JavaScript beacon с временем на странице

### 3. Трекинг конверсии (из вашей lootbox системы)

Когда пользователь покупает лутбокс, вызовите webhook:

```bash
curl -X POST "http://localhost:8000/api/v1/utm/track/conversion" \
  -H "Content-Type: application/json" \
  -d '{
    "traffic_source_id": "uuid-from-tracking",
    "conversion_type": "purchase",
    "amount": 5000,
    "currency": "USD",
    "product_id": "lootbox_gold",
    "product_name": "Gold Lootbox",
    "customer_id": "customer_123",
    "metadata": {
      "payment_method": "stripe",
      "transaction_id": "txn_abc123"
    }
  }'
```

**Как получить `traffic_source_id`?**

Вариант 1: Сохранить UTM параметры в Telegram bot при старте:
```python
# В вашем Telegram боте
@bot.message_handler(commands=['start'])
def start(message):
    # Извлечь UTM параметры из deep link
    utm_id = extract_utm_from_start_param(message.text)

    # Сохранить в БД/Redis для этого user_id
    save_utm_for_user(message.from_user.id, utm_id)
```

Вариант 2: Передать через URL параметр в Telegram:
```
https://t.me/sportschannel?start=utm_tiktok_a7b3c_8f2e1
```

### 4. Просмотр аналитики

**Dashboard (общая статистика):**
```bash
curl "http://localhost:8000/api/v1/analytics/dashboard?date_from=2025-01-01" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Ответ:
```json
{
  "success": true,
  "period": {"from": "2025-01-01", "to": "2025-02-02"},
  "summary": {
    "total_clicks": 1500,
    "total_conversions": 75,
    "total_revenue": 3750.00,
    "conversion_rate": 5.0,
    "avg_order_value": 50.00
  },
  "top_sources": [
    {
      "source": "tiktok",
      "clicks": 1200,
      "conversions": 60,
      "revenue": 3000.00,
      "conversion_rate": 5.0
    }
  ],
  "daily_stats": [...]
}
```

**Аналитика конкретной кампании:**
```bash
curl "http://localhost:8000/api/v1/analytics/campaign/football_jan_2025" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Воронка конверсии:**
```bash
curl "http://localhost:8000/api/v1/analytics/funnel" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Интеграция с TikTok

### Workflow создания TikTok видео с трекингом:

1. **Создать видео** (нарезать из исходника)
2. **Сгенерировать UTM ссылку** через API
3. **Вставить ссылку** в TikTok bio или закрепленный комментарий
4. **Опубликовать видео** в TikTok
5. **Отслеживать метрики** через аналитику

### Пример автоматизации:

```python
import requests

# 1. Генерация UTM ссылки
response = requests.post(
    "http://localhost:8000/api/v1/utm/generate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "base_url": "http://yourdomain.com/api/v1/landing/l",
        "source": "tiktok",
        "campaign": "football_highlights",
        "content": f"video_{video_id}",
    }
)

utm_data = response.json()
tracking_link = utm_data["utm_link"]

# 2. Создать TikTok видео с этой ссылкой
tiktok_caption = f"""
⚽ INCREDIBLE GOAL! 🔥

Follow for daily highlights!

Link: {tracking_link}

#football #soccer #goals #fyp
"""

# 3. Загрузить на TikTok
upload_to_tiktok(video_path, caption=tiktok_caption)
```

---

## Модели данных

### TrafficSource
Хранит UTM параметры и клики:
- `utm_source`, `utm_campaign`, `utm_content` - UTM параметры
- `clicks` - количество кликов
- `conversions` - количество конверсий
- `revenue` - общий доход (в центах)
- `device_type`, `browser`, `os` - информация об устройстве
- `country`, `city` - геолокация

### Conversion
Хранит данные о покупках:
- `traffic_source_id` - ссылка на источник трафика
- `amount` - сумма покупки (в центах)
- `conversion_type` - тип конверсии (purchase, signup, etc.)
- `time_to_conversion` - время от клика до покупки (секунды)
- `metadata` - дополнительные данные (JSON)

### TikTokVideo
Информация о TikTok видео:
- `caption`, `hashtags` - контент видео
- `utm_campaign` - связь с кампанией
- `tracking_link` - UTM ссылка для этого видео
- `views`, `likes`, `comments`, `shares` - метрики TikTok
- `status` - статус (draft, scheduled, published)

---

## Дашборд (Frontend)

Вы можете создать React/Vue дашборд, используя API endpoints:

```javascript
// Fetch dashboard data
const response = await fetch('/api/v1/analytics/dashboard', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();

// Display charts:
// - Total clicks/conversions/revenue
// - Top sources (TikTok vs Instagram)
// - Daily trend line
// - Conversion funnel
// - Device breakdown
```

Или использовать готовые библиотеки:
- **Chart.js** для графиков
- **Recharts** для React
- **ApexCharts** для интерактивных дашбордов

---

## Best Practices

### 1. Naming conventions для кампаний

Используйте понятные названия:
```
{sport}_{type}_{month}_{year}
football_highlights_jan_2025
basketball_top10_feb_2025
```

### 2. UTM content

Используйте `utm_content` для A/B тестирования:
```
content: "video_123"           # ID видео
content: "hook_wait_for_it"    # Тип хука
content: "cta_join_now"        # Вариант CTA
```

### 3. Промежуточная страница

Преимущества landing page:
- Трекинг без TikTok API
- Возможность показать дополнительную информацию
- A/B тестирование дизайна
- Сбор email (опционально)

### 4. Конверсии

Трекайте разные типы конверсий:
- `signup` - регистрация в боте
- `deposit` - первый депозит
- `purchase` - покупка лутбокса
- `repeat_purchase` - повторная покупка

---

## Troubleshooting

### Проблема: Клики не трекаются

Проверьте:
1. БД доступна: `psql -U user -d tg_reposter -c "SELECT 1"`
2. API запущен: `curl http://localhost:8000/health`
3. UTM ID существует в БД:
   ```sql
   SELECT * FROM traffic_sources WHERE utm_id = 'your_utm_id';
   ```

### Проблема: Конверсии не связываются с источником

Убедитесь что:
1. Вы сохраняете `utm_id` при старте Telegram бота
2. При конверсии передаёте правильный `traffic_source_id`
3. В БД есть запись в таблице `traffic_sources`

---

## Roadmap

Следующие шаги (из вашего плана):

### Milestone 2: Масштабирование трафика
- [ ] Кросс-промо между каналами
- [ ] Telegram Ads интеграция
- [ ] Автоматический контент-план
- [ ] A/B тестирование CTA

### Milestone 3: Оптимизация конверсий
- [ ] Прогрев аудитории (воронка)
- [ ] Ретаргетинг в боте
- [ ] Персональные промокоды
- [ ] Расширенная аналитика

---

## Полезные команды

```bash
# Проверить статус API
curl http://localhost:8000/health

# Посмотреть все UTM источники
curl http://localhost:8000/api/v1/utm/sources \
  -H "Authorization: Bearer $TOKEN"

# Посмотреть конверсии
curl http://localhost:8000/api/v1/utm/conversions \
  -H "Authorization: Bearer $TOKEN"

# Сравнить источники трафика
curl "http://localhost:8000/api/v1/analytics/sources/compare?sources=tiktok&sources=instagram" \
  -H "Authorization: Bearer $TOKEN"

# Временной ряд (по дням)
curl "http://localhost:8000/api/v1/analytics/time-series?granularity=day" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Вопросы?

Документация API: `http://localhost:8000/docs`

OpenAPI спецификация: `http://localhost:8000/redoc`
