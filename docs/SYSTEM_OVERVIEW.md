# TikTok → Telegram → Lootbox - Полная система трекинга

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    TikTok Video                             │
│              (ссылка в bio/комментарии)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ UTM Link (yourdomain.com/l/tiktok_abc)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Landing Page (промежуточная)                    │
│  • Красивая страница с описанием канала                     │
│  • Автоматический редирект через 3 сек                      │
│  • Трекинг: device, geo, время на странице                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Redirect to Telegram
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         Telegram Channel (t.me/sportschannel)               │
│  • Автопостинг контента                                     │
│  • CTA в постах → ссылка на бота                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Deep Link (/start utm_xxx)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Lootbox Bot (пользовательский)                 │
│  • Сохранение UTM для user_id                               │
│  • Покупка лутбокса                                         │
│  • track_conversion() → API                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Webhook
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Tracking API (FastAPI)                         │
│  • UTM генерация                                            │
│  • Трекинг кликов и конверсий                               │
│  • Аналитика                                                │
│  • База данных (PostgreSQL)                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ API Calls
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Admin Bot (Telegram)                           │
│  • /generate - создать UTM ссылки                           │
│  • /stats - просмотр аналитики                              │
│  • /campaigns - управление кампаниями                       │
│  • Уведомления о конверсиях                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Компоненты системы

### 1. Tracking API (FastAPI)

**Файл:** `api/main.py`

**Роутеры:**
- `/api/v1/utm/` - генерация UTM, трекинг
- `/api/v1/analytics/` - дашборд, воронка, сравнение
- `/api/v1/landing/` - промежуточные страницы
- `/api/v1/auth/` - аутентификация

**База данных:**
- `TrafficSource` - UTM метки и клики
- `Conversion` - конверсии (покупки)
- `TikTokVideo` - видео для TikTok
- `TikTokAccount` - аккаунты TikTok
- `ContentTemplate` - шаблоны контента

**Запуск:**
```bash
python api/main.py
# http://localhost:8000
```

---

### 2. Admin Bot (Telegram)

**Файл:** `admin_bot.py`

**Команды:**
- `/generate` - создать UTM ссылку
- `/stats` - статистика
- `/campaigns` - список кампаний
- `/top` - топ источников
- `/conversions` - последние покупки
- `/settings` - настройки уведомлений

**Функции:**
- Интерактивная генерация UTM
- Просмотр аналитики в реальном времени
- Ежедневные отчёты в 9:00
- Уведомления о конверсиях

**Запуск:**
```bash
python admin_bot.py
```

---

### 3. User Bot (Lootbox)

**Файл:** `telegram_bot_integration.py`

**Интеграция:**
- Обработка `/start` с UTM параметрами
- Сохранение UTM → user_id
- Трекинг конверсий при покупке
- Примеры для Stripe, Telegram Stars

**Использование:**
```python
from telegram_bot_integration import save_utm_for_user, track_conversion

# В /start
save_utm_for_user(user_id, utm_id, traffic_source_id)

# При покупке
track_conversion(user_id, amount, product_id, product_name)
```

---

### 4. Landing Pages

**Файл:** `api/routers/landing.py`

**Endpoints:**
- `GET /api/v1/landing/l/{utm_id}` - промежуточная страница
- `POST /api/v1/landing/track-time` - трекинг времени
- `GET /api/v1/landing/preview` - предпросмотр

**Функции:**
- Красивый дизайн с градиентом
- Авто-редирект через 3 сек
- JavaScript трекинг
- Mobile-responsive

---

## Установка и запуск

### Требования

- Python 3.11+
- PostgreSQL
- Redis (опционально)

### Шаг 1: Установка

```bash
# Клонировать репозиторий
git clone ...
cd tg-reposter

# Установить зависимости
pip install -r requirements.txt

# Создать БД
createdb tg_reposter
```

### Шаг 2: Конфигурация

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env
nano .env
```

Обязательные переменные:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/tg_reposter

# Admin Bot
ADMIN_BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_telegram_id

# Tracking API
LANDING_BASE_URL=https://yourdomain.com/api/v1/landing/l
DEFAULT_TELEGRAM_CHANNEL=https://t.me/sportschannel
```

### Шаг 3: Создать таблицы

```python
from database.base import Base, engine
from database.models import *
Base.metadata.create_all(bind=engine)
```

### Шаг 4: Запустить

```bash
# Terminal 1: Tracking API
python api/main.py

# Terminal 2: Admin Bot
python admin_bot.py

# Terminal 3: User Bot (если есть)
python your_lootbox_bot.py
```

---

## Использование

### Создание кампании

#### 1. Генерация UTM ссылки

В Admin Bot:
```
/generate
→ football_jan_2025
→ TikTok
→ video_messi_goal

Результат:
https://yourdomain.com/l/tiktok_abc123
```

#### 2. Публикация в TikTok

1. Создать видео
2. Вставить ссылку в био: `https://yourdomain.com/l/tiktok_abc123`
3. Опубликовать

#### 3. Трекинг результатов

В Admin Bot:
```
/stats → Сегодня
/campaigns → football_jan_2025
/top
```

---

## Метрики

### Ключевые показатели

**Клики:**
- Сколько человек перешло с TikTok на landing page

**Конверсии:**
- Сколько человек купило лутбокс

**Conversion Rate (CR):**
- % конверсии от кликов
- Формула: (конверсии / клики) × 100

**Average Order Value (AOV):**
- Средний чек
- Формула: выручка / конверсии

**ROI:**
- Возврат инвестиций
- Формула: (выручка - расходы) / расходы × 100

### Пример расчёта

```
За месяц:
- TikTok видео: 20 штук
- Просмотры: 100,000
- Клики: 2,000 (CTR: 2%)
- Конверсии: 100 (CR: 5%)
- Выручка: $5,000
- AOV: $50

Расходы:
- Telegram Ads: $500
- Контент: $200
= $700 total

ROI:
($5,000 - $700) / $700 × 100 = 614% 🚀
```

---

## Файлы проекта

### API
```
api/
├── main.py              # FastAPI приложение
├── dependencies.py      # Зависимости (auth)
└── routers/
    ├── auth.py          # Аутентификация
    ├── utm.py           # UTM трекинг
    ├── analytics.py     # Аналитика
    └── landing.py       # Landing pages
```

### Database
```
database/
├── base.py              # SQLAlchemy setup
├── models.py            # ORM модели
└── schemas.py           # Pydantic схемы
```

### Bots
```
admin_bot.py                    # Admin бот
telegram_bot_integration.py     # User бот (интеграция)
```

### Документация
```
UTM_TRACKING_README.md          # Полная документация API
TELEGRAM_BOT_INTEGRATION.md     # Интеграция user бота
ADMIN_BOT_README.md             # Документация admin бота
ADMIN_BOT_QUICKSTART.md         # Быстрый старт
QUICKSTART.md                   # Общий быстрый старт
SYSTEM_OVERVIEW.md              # Этот файл
```

---

## Roadmap

### Phase 1: MVP (Готово!) ✅
- UTM генерация и трекинг
- Landing pages
- Базовая аналитика
- Admin Bot
- Интеграция с user ботом

### Phase 2: Видео автоматизация
- [ ] Нарезчик видео для TikTok
- [ ] Автоматическое создание контента
- [ ] Генерация captions через AI
- [ ] Планировщик постинга

### Phase 3: Оптимизация
- [ ] A/B тестирование landing pages
- [ ] A/B тестирование CTA
- [ ] Автоматические рекомендации
- [ ] Predictive analytics

### Phase 4: Масштабирование
- [ ] Multi-tenant SaaS
- [ ] Web dashboard (React)
- [ ] Интеграция с Google Analytics
- [ ] Экспорт в Excel/CSV

---

## Поддержка

**Документация:**
- [UTM Tracking](./UTM_TRACKING_README.md)
- [Admin Bot](./ADMIN_BOT_README.md)
- [Telegram Integration](./TELEGRAM_BOT_INTEGRATION.md)

**Быстрый старт:**
- [General Quickstart](./QUICKSTART.md)
- [Admin Bot Quickstart](./ADMIN_BOT_QUICKSTART.md)

**API Docs:**
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Лицензия

MIT License

---

Готово! 🚀 Полная система трекинга от TikTok до покупки лутбокса!
