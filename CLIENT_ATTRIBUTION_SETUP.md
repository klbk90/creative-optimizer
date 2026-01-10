# 🔗 Client Attribution Setup - Как подключить клиента

## 🎯 Цель

Клиент (EdTech компания) хочет:
1. Тестировать свои креативы через micro-influencers
2. Получать точную атрибуцию конверсий
3. Видеть, какой паттерн работает лучше

## 📊 Архитектура (что уже есть)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                             │
└─────────────────────────────────────────────────────────────────┘

1. Instagram Post (Influencer)
   ↓
   Link: https://your-domain.com/api/v1/edtech/landing?utm_id=inf_creator_123
   ↓

2. Landing Page (ВАШ API)
   ├── Извлекает UTM (inf_creator_123)
   ├── Инициализирует RudderStack (anonymousId: anon_XYZ789)
   ├── Отправляет Page Viewed → RudderStack
   └── RudderStack Webhook → ВАШ API → Создает UserSession в БД

3. User покупает через 2 дня
   ├── Заполняет форму checkout (email, name)
   ├── Нажимает "Enroll Now"
   ├── Frontend отправляет POST /api/v1/edtech/checkout
   └── Frontend отправляет Order Completed → RudderStack
       ↓
       RudderStack Webhook → ВАШ API → Находит UserSession → Создает Conversion

4. ВАШ API
   ├── Обновляет TrafficSource (conversions++, revenue++)
   ├── Обновляет PatternPerformance (Bayesian CVR update)
   └── Клиент получает данные через GET /api/v1/analytics
```

---

## 🔧 Два варианта интеграции для клиента

### Вариант 1: **Полностью через ВАШУ систему** (рекомендуется)

**Что нужно клиенту:**
- Ничего! Вы даете ему landing page URL.

**Ваши API endpoints:**

```
1. GET /api/v1/edtech/landing?utm_id={utm_id}&pain_point={pain}&course={course}
   → Отдает HTML лендинга со встроенным RudderStack

2. POST /api/v1/edtech/checkout
   → Обрабатывает покупку (в MVP - mock payment)

3. POST /api/v1/rudderstack/track
   → Webhook от RudderStack (Page Viewed, Order Completed)

4. GET /api/v1/analytics/...
   → Клиент получает свою статистику
```

**Плюсы:**
✅ Клиент ничего не настраивает (plug & play)
✅ Вы контролируете весь флоу
✅ Attribution гарантированно работает

**Минусы:**
❌ Клиент должен доверить вам свой checkout

---

### Вариант 2: **Клиент использует свой checkout** (hybrid)

**Что происходит:**
- Landing page → ВАШ API (для UTM tracking)
- Checkout → ИХ сайт (для payment)
- Attribution → ВАШ API (через RudderStack server-side)

**Что нужно клиенту:**

1. **Установить RudderStack SDK на своем сайте:**

```html
<!-- На их checkout странице -->
<script>
rudderanalytics=window.rudderanalytics=[];for(var methods=["load","page","track",...],i=0;i<methods.length;i++){...}
</script>
<script src="https://cdn.rudderlabs.com/v1.1/rudder-analytics.min.js"></script>

<script>
  // Инициализация RudderStack
  rudderanalytics.load(
    'YOUR_RUDDERSTACK_WRITE_KEY',  // ⭐ ВАШ write key
    'YOUR_RUDDERSTACK_DATA_PLANE_URL'
  );
</script>
```

2. **Пробросить anonymousId из вашего лендинга в их checkout:**

```javascript
// На вашем лендинге (перед редиректом на их checkout)
const anonymousId = rudderanalytics.getAnonymousId();
const utmId = getStoredUtm()?.utm_id;

// Redirect на их checkout с параметрами
window.location.href = `https://client-site.com/checkout?anon_id=${anonymousId}&utm_id=${utmId}`;
```

3. **На их checkout странице восстановить anonymousId:**

```javascript
// Извлечь из URL
const urlParams = new URLSearchParams(window.location.search);
const anonId = urlParams.get('anon_id');
const utmId = urlParams.get('utm_id');

// Установить в RudderStack
if (anonId) {
  rudderanalytics.setAnonymousId(anonId);
}

// Сохранить UTM
if (utmId) {
  localStorage.setItem('utm_id', utmId);
}
```

4. **После успешной оплаты отправить Order Completed:**

```javascript
// После successful payment
rudderanalytics.track('Order Completed', {
  order_id: orderData.id,
  total: orderData.total,
  currency: 'USD',
  product_name: orderData.productName,
  utm_id: localStorage.getItem('utm_id'),  // ⭐ ВАЖНО
});
```

**Результат:**
- RudderStack webhook отправит Order Completed → ВАШ API
- ВАШ API найдет UserSession по anonymousId
- Атрибуция сработает ✅

**Плюсы:**
✅ Клиент контролирует payment
✅ Attribution все равно работает

**Минусы:**
❌ Клиент должен интегрировать RudderStack
❌ Больше точек отказа (если клиент ошибется)

---

## 🚀 Рекомендуемая архитектура (Вариант 1 + White Label)

### Что вы предоставляете клиенту:

**1. API Endpoints для статистики:**

```python
# GET /api/v1/analytics/creatives
{
  "creatives": [
    {
      "id": "creative-uuid",
      "name": "Python Course - No Time Pain",
      "conversions": 15,
      "clicks": 100,
      "cvr": 15.0,
      "revenue": 735.00,
      "pattern": {
        "hook_type": "question",
        "emotion": "curiosity",
        "pain_point": "no_time"
      }
    }
  ]
}

# GET /api/v1/analytics/influencers
{
  "influencers": [
    {
      "handle": "edutech_creator_1",
      "followers": 15000,
      "clicks": 25,
      "conversions": 4,
      "cvr": 16.0,
      "revenue": 196.00,
      "roi": 3.92  # (revenue / cost)
    }
  ]
}

# GET /api/v1/rudderstack/thompson-sampling?product_category=programming
{
  "recommendations": [
    {
      "hook_type": "question",
      "emotion": "curiosity",
      "mean_cvr": 0.15,
      "sample_size": 10,
      "reasoning": "High confidence winner"
    }
  ]
}
```

**2. White-label Landing Pages:**

Клиент может кастомизировать:
- Брендинг (логотип, цвета)
- Контент (headline, benefits)
- Домен (custom domain через CNAME)

```python
# GET /api/v1/edtech/landing?utm_id=xxx&client_id=client_abc

# В базе:
class Client:
    branding = {
        "logo_url": "https://client.com/logo.png",
        "primary_color": "#FF5733",
        "domain": "learn.client.com"
    }
```

---

## 🔑 Что нужно ОТ клиента (минимум)

### Для Варианта 1 (рекомендуемый):

1. **Креативы (видео)** → вы загружаете через `/api/v1/creatives/upload`
2. **Product info:**
   - Название курса
   - Цена
   - Target audience pain point
3. **Payment gateway credentials** (опционально):
   - Stripe API key (если вы обрабатываете payment)
   - Или webhook endpoint для их payment системы

**ВСЁ!** Остальное вы делаете сами.

---

## 💡 Пример: Полный цикл для клиента

### Шаг 1: Клиент загружает креатив

```bash
# Через ваш API (или frontend dashboard)
POST /api/v1/creatives

{
  "name": "Python Course - No Time Pain",
  "video_url": "https://vimeo.com/video123",
  "product_category": "programming",
  "pain_point": "no_time",
  "price": 49.00
}

# Ответ:
{
  "creative_id": "creative-abc123",
  "status": "ready"
}
```

---

### Шаг 2: Вы находите micro-influencers

```python
# Автоматически через Modash API
from utils.modash_client import ModashClient

client = ModashClient()
influencers = client.search_edtech_influencers(
    niche="programming",
    limit=20
)

# Создаете traffic sources
for inf in influencers:
    utm_id = f"inf_{inf['username']}_{uuid.uuid4().hex[:6]}"

    # Создаете landing page URL
    landing_url = f"https://your-domain.com/api/v1/edtech/landing?utm_id={utm_id}&pain_point=no_time&course=python"

    # Отправляете outreach email
    send_email(
        to=inf['email'],
        subject="Collaboration opportunity",
        body=f"Your unique link: {landing_url}"
    )
```

---

### Шаг 3: Influencer публикует пост

```
Instagram post by @edutech_creator_1:
"Learn Python in 15 min/day! 🔥
Link in bio: https://your-domain.com/api/v1/edtech/landing?utm_id=inf_edutech_creator_1_abc123"
```

---

### Шаг 4: User кликает, покупает

**RudderStack автоматически:**
1. Page Viewed → ваш API → UserSession создается
2. Order Completed → ваш API → Conversion создается + Bayesian update

---

### Шаг 5: Клиент смотрит статистику

```bash
# Через ваш dashboard или API
GET /api/v1/analytics/creatives?user_id=client_abc

# Результат:
{
  "summary": {
    "total_clicks": 500,
    "total_conversions": 75,
    "total_revenue": 3675.00,
    "avg_cvr": 15.0
  },
  "best_pattern": {
    "hook_type": "question",
    "emotion": "curiosity",
    "pain_point": "no_time",
    "cvr": 17.5,
    "confidence_interval": [12.3, 23.1]
  },
  "recommendation": "Scale this pattern to Facebook Ads"
}
```

---

## 🎨 White-label Dashboard (опционально)

Если хотите дать клиенту UI (вместо API):

**Уже есть frontend:**
```
/Users/aliakseiramanchyk/creative-optimizer/frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx     # Общая статистика
│   │   ├── Creatives.jsx     # Список креативов
│   │   ├── Analytics.jsx     # Графики
│   │   └── Patterns.jsx      # Thompson Sampling recommendations
```

**Нужно добавить:**
1. Multi-tenancy (user_id filter)
2. Authentication (JWT tokens)
3. Custom branding per client

---

## ✅ Итого: Что ОБЯЗАТЕЛЬНО нужно для работы attribution

### На вашей стороне (уже есть ✅):

1. **RudderStack account:**
   - Write Key
   - Data Plane URL
   - Webhook destination → ваш API

2. **API endpoints:**
   - `/api/v1/edtech/landing` - лендинг с RudderStack SDK
   - `/api/v1/rudderstack/track` - webhook для событий
   - `/api/v1/edtech/checkout` - обработка покупки (опционально)

3. **Database:**
   - UserSession (для attribution)
   - TrafficSource (UTM tracking)
   - Conversion (покупки)
   - PatternPerformance (Bayesian updates)

### От клиента (минимум):

**Вариант 1 (plug & play):**
- Креативы (видео)
- Product info (название, цена, pain point)
- ВСЁ!

**Вариант 2 (их checkout):**
- Креативы
- Интеграция RudderStack на их сайте (10 строк кода)
- Пробросить anonymousId

---

## 🚀 Запуск production

```bash
# 1. Настроить .env
RUDDERSTACK_WRITE_KEY=your_key
RUDDERSTACK_DATA_PLANE_URL=https://your-instance.dataplane.rudderstack.com

# 2. Запустить API
docker-compose up -d

# 3. Открыть лендинг
https://your-domain.com/api/v1/edtech/landing?utm_id=test_123&pain_point=no_time

# 4. Проверить RudderStack Live Events
# Page Viewed должен появиться

# 5. Купить на лендинге
# Order Completed должен появиться

# 6. Проверить БД
SELECT * FROM user_sessions WHERE utm_id = 'test_123';
SELECT * FROM conversions WHERE traffic_source_id = (SELECT id FROM traffic_sources WHERE utm_id = 'test_123');

# ✅ Если данные есть → attribution работает!
```

---

## 📞 Что сказать клиенту

**"Мы даем вам полностью готовое решение для тестирования креативов:**

1. Загружаете видео → мы находим 20 micro-influencers
2. Мы создаем персональные landing pages с UTM tracking
3. Influencers публикуют посты с вашими ссылками
4. Мы автоматически трекаем все конверсии (даже через неделю!)
5. Через 7 дней вы получаете отчет: какой паттерн работает лучше
6. Масштабируете winning pattern на Facebook/TikTok Ads

**Ваша задача:** Просто загрузить креативы. Всё остальное - наша."**

Хотите ли plug & play (мы всё делаем) или hybrid (вы контролируете checkout)?
