# Быстрый старт UTM трекинга

## 1. Установка (2 минуты)

```bash
# Установить зависимости
pip install -r requirements.txt

# Создать БД
createdb tg_reposter
```

## 2. Настройка .env

```env
DATABASE_URL=postgresql://user:password@localhost:5432/tg_reposter
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-change-this
DEFAULT_TELEGRAM_CHANNEL=https://t.me/sportschannel
```

## 3. Создать таблицы

```python
# В Python console
from database.base import Base, engine
from database.models import *
Base.metadata.create_all(bind=engine)
```

## 4. Запустить API

```bash
python api/main.py
```

API доступно на `http://localhost:8000`

Документация: `http://localhost:8000/docs`

---

## Тестирование

### 1. Посмотреть preview landing page

Откройте в браузере:
```
http://localhost:8000/api/v1/landing/preview
```

### 2. Создать тестового пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### 3. Получить токен

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

Скопируйте `access_token` из ответа.

### 4. Сгенерировать UTM ссылку

```bash
export TOKEN="your-access-token-here"

curl -X POST "http://localhost:8000/api/v1/utm/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "http://localhost:8000/api/v1/landing/l",
    "source": "tiktok",
    "campaign": "test_campaign",
    "content": "video_123"
  }'
```

Вы получите:
```json
{
  "success": true,
  "utm_link": "http://localhost:8000/api/v1/landing/l/tiktok_xxxxx_xxxxx",
  "utm_id": "tiktok_xxxxx_xxxxx"
}
```

### 5. Протестировать landing page

Откройте `utm_link` в браузере. Вы увидите:
- Красивую landing page
- Авто-редирект через 3 секунды
- Клик автоматически записался в БД!

### 6. Проверить трекинг

```bash
curl "http://localhost:8000/api/v1/utm/sources" \
  -H "Authorization: Bearer $TOKEN"
```

Вы увидите ваш клик!

### 7. Посмотреть аналитику

```bash
curl "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Что дальше?

1. **Интеграция с TikTok**: Добавьте UTM ссылки в TikTok bio
2. **Webhook конверсий**: Настройте webhook из lootbox системы
3. **Dashboard**: Создайте React/Vue frontend для красивой аналитики
4. **Видео нарезчик**: Следующий шаг - автоматизация создания TikTok контента

Полная документация: [UTM_TRACKING_README.md](./UTM_TRACKING_README.md)
