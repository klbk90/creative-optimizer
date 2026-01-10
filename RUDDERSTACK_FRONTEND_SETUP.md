# 🔗 RudderStack Frontend Setup - Attribution Glue

## ⚠️ КРИТИЧЕСКИ ВАЖНО

**external_id (anonymousId)** - это ключ к правильной атрибуции конверсий.

Если юзер перейдет по ссылке инфлюенсера, а потом купит через **2 дня**, `external_id` должен остаться **тем же**.

---

## 📊 Как работает attribution

```
День 1:
  User кликает по ссылке инфлюенсера: utm_id=inf_creator_abc123
  ↓
  RudderStack: anonymousId = "anon_XYZ789" (cookie/localStorage)
  ↓
  Event: Page Viewed { utm_id, anonymousId: "anon_XYZ789" }
  ↓
  Backend создает UserSession:
    - customer_id = "anon_XYZ789"
    - utm_id = "inf_creator_abc123"
    - creative_id = "creative-uuid"

День 3:
  User возвращается и покупает
  ↓
  RudderStack: anonymousId = "anon_XYZ789" (тот же!)
  ↓
  Event: Order Completed { anonymousId: "anon_XYZ789" }
  ↓
  Backend находит UserSession по customer_id="anon_XYZ789"
  ↓
  ✅ Атрибуция к правильному utm_id и creative!
```

---

## 🛠 Setup Instructions

### 1. Установить RudderStack SDK

**Для статичного лендинга (HTML + JS):**

```html
<!-- В <head> вашего лендинга -->
<script>
rudderanalytics=window.rudderanalytics=[];for(var methods=["load","page","track","identify","alias","group","ready","reset","getAnonymousId","setAnonymousId"],i=0;i<methods.length;i++){var method=methods[i];rudderanalytics[method]=function(a){return function(){rudderanalytics.push([a].concat(Array.prototype.slice.call(arguments)))}}(method)}rudderanalytics.load("YOUR_WRITE_KEY","YOUR_DATA_PLANE_URL"),rudderanalytics.page();
</script>
<script src="https://cdn.rudderlabs.com/v1.1/rudder-analytics.min.js"></script>
```

**Для React/Next.js:**

```bash
npm install rudder-sdk-js
```

```javascript
// utils/analytics.js
import * as rudderanalytics from 'rudder-sdk-js';

rudderanalytics.load(
  process.env.NEXT_PUBLIC_RUDDERSTACK_WRITE_KEY,
  process.env.NEXT_PUBLIC_RUDDERSTACK_DATA_PLANE_URL,
  {
    // ⭐ КРИТИЧЕСКИ ВАЖНО: настройки persistence
    cookieConsentManager: {
      storage: 'localStorage', // Или 'cookie'
    },
    // Длительность хранения anonymousId
    cookieDuration: 31536000000, // 1 год в миллисекундах
  }
);

export default rudderanalytics;
```

---

### 2. Настроить persistence для anonymousId

**⚠️ БЕЗ ЭТОГО ATTRIBUTION НЕ СРАБОТАЕТ!**

RudderStack должен сохранять `anonymousId` в cookie или localStorage, чтобы он **не менялся** между визитами.

**Проверка в browser console:**

```javascript
// Получить anonymousId
rudderanalytics.getAnonymousId()
// → "anon_XYZ789"

// Убедиться, что он сохранен
localStorage.getItem('rl_anonymous_id')
// → "anon_XYZ789"
```

**Если anonymousId меняется при каждом визите:**

```javascript
// Явно установить anonymousId из cookie/localStorage
const storedId = localStorage.getItem('my_custom_anon_id');

if (storedId) {
  rudderanalytics.setAnonymousId(storedId);
} else {
  const newId = rudderanalytics.getAnonymousId();
  localStorage.setItem('my_custom_anon_id', newId);
}
```

---

### 3. Трекинг UTM параметров (Page Viewed)

**Извлечь UTM из URL:**

```javascript
// utils/utm.js
export function getUtmParams() {
  const urlParams = new URLSearchParams(window.location.search);

  return {
    utm_source: urlParams.get('utm_source'),
    utm_medium: urlParams.get('utm_medium'),
    utm_campaign: urlParams.get('utm_campaign'),
    utm_content: urlParams.get('utm_content'),
    utm_id: urlParams.get('utm_id'), // ⭐ КЛЮЧЕВОЙ ПАРАМЕТР
  };
}

export function saveUtmToStorage(utmParams) {
  // Сохранить UTM на 30 дней
  const expiry = Date.now() + (30 * 24 * 60 * 60 * 1000);

  localStorage.setItem('utm_params', JSON.stringify({
    ...utmParams,
    expiry
  }));
}

export function getStoredUtm() {
  const stored = localStorage.getItem('utm_params');

  if (!stored) return null;

  const { expiry, ...utmParams } = JSON.parse(stored);

  // Проверить, не истек ли срок
  if (Date.now() > expiry) {
    localStorage.removeItem('utm_params');
    return null;
  }

  return utmParams;
}
```

**Отправить Page Viewed event:**

```javascript
// pages/index.js (или ваш лендинг)
import rudderanalytics from '../utils/analytics';
import { getUtmParams, saveUtmToStorage, getStoredUtm } from '../utils/utm';

useEffect(() => {
  // Извлечь UTM из URL
  const utmParams = getUtmParams();

  // Если есть utm_id в URL - сохранить
  if (utmParams.utm_id) {
    saveUtmToStorage(utmParams);
  }

  // Получить UTM (из URL или из storage)
  const finalUtm = utmParams.utm_id ? utmParams : getStoredUtm();

  // Отправить Page Viewed event
  rudderanalytics.page({
    properties: {
      ...finalUtm,
      page_url: window.location.href,
      referrer: document.referrer,
    }
  });
}, []);
```

**⭐ Результат:**

```json
{
  "event": "Page Viewed",
  "anonymousId": "anon_XYZ789",
  "properties": {
    "utm_id": "inf_creator_abc123",
    "utm_source": "instagram",
    "utm_medium": "influencer",
    "utm_campaign": "edtech_jan_2026",
    "page_url": "https://yoursite.com/landing",
    "referrer": "https://instagram.com"
  }
}
```

---

### 4. Трекинг конверсий (Order Completed)

**После успешной покупки:**

```javascript
// pages/checkout/success.js
import rudderanalytics from '../../utils/analytics';
import { getStoredUtm } from '../../utils/utm';

function handlePurchaseSuccess(orderData) {
  // Получить UTM (для дополнительного контекста)
  const utmParams = getStoredUtm();

  // Отправить Order Completed event
  rudderanalytics.track('Order Completed', {
    order_id: orderData.id,
    total: orderData.total,
    currency: 'USD',
    product_name: orderData.product_name,
    product_id: orderData.product_id,

    // ⭐ Опционально: передать UTM для fallback attribution
    utm_id: utmParams?.utm_id,
    utm_source: utmParams?.utm_source,
    utm_campaign: utmParams?.utm_campaign,
  });

  console.log('✅ Conversion tracked!');
}
```

**⭐ Результат:**

```json
{
  "event": "Order Completed",
  "anonymousId": "anon_XYZ789",
  "properties": {
    "order_id": "ord_123",
    "total": 49.00,
    "currency": "USD",
    "product_name": "Python Course",
    "utm_id": "inf_creator_abc123"
  }
}
```

---

### 5. Identify пользователя (опционально)

Если пользователь регистрируется/логинится:

```javascript
// После регистрации/логина
rudderanalytics.identify(userId, {
  email: user.email,
  name: user.name,
  created_at: user.createdAt,
});
```

**⭐ Это свяжет `anonymousId` с `userId`:**

```
anonymousId="anon_XYZ789" → userId="user_123"
```

Теперь в событиях будет и `anonymousId`, и `userId`:

```json
{
  "event": "Order Completed",
  "userId": "user_123",
  "anonymousId": "anon_XYZ789",
  "properties": {...}
}
```

---

## 🧪 Тестирование Attribution

### 1. Проверить сохранение anonymousId

```javascript
// Browser console
console.log('AnonymousId:', rudderanalytics.getAnonymousId());

// Перезагрузить страницу
location.reload();

// Проверить, что ID остался тем же
console.log('AnonymousId после reload:', rudderanalytics.getAnonymousId());
```

**✅ Ожидаемое поведение:**
```
AnonymousId: anon_XYZ789
AnonymousId после reload: anon_XYZ789  (тот же!)
```

---

### 2. Проверить UTM persistence

```javascript
// 1. Открыть лендинг с UTM:
// https://yoursite.com/?utm_id=inf_test_123

// 2. Проверить, что UTM сохранен
console.log('Stored UTM:', localStorage.getItem('utm_params'));

// 3. Перейти на другую страницу (без UTM)
// https://yoursite.com/about

// 4. Проверить, что UTM все еще есть
const { getStoredUtm } = require('./utils/utm');
console.log('UTM на странице /about:', getStoredUtm());
```

**✅ Ожидаемое поведение:**
```
Stored UTM: {"utm_id":"inf_test_123", "expiry":1234567890}
UTM на странице /about: {utm_id: "inf_test_123"}
```

---

### 3. E2E тест attribution

**Сценарий:**

```
День 1:
  1. User кликает по ссылке: /?utm_id=inf_test_123
  2. RudderStack: Page Viewed { utm_id: "inf_test_123", anonymousId: "anon_ABC" }
  3. Backend создает UserSession

День 3:
  1. User возвращается (без UTM)
  2. User покупает курс
  3. RudderStack: Order Completed { anonymousId: "anon_ABC" }
  4. Backend находит UserSession по anonymousId="anon_ABC"
  5. ✅ Конверсия атрибутирована к utm_id="inf_test_123"
```

**Проверка в базе данных:**

```sql
-- 1. Проверить UserSession
SELECT * FROM user_sessions WHERE external_id = 'anon_ABC';
-- Результат: utm_id = 'inf_test_123'

-- 2. Проверить Conversion
SELECT * FROM conversions WHERE external_id = 'anon_ABC';
-- Результат: traffic_source_id = <id из user_sessions>

-- 3. Проверить TrafficSource
SELECT * FROM traffic_sources WHERE utm_id = 'inf_test_123';
-- Результат: conversions = 1, revenue = 4900 (cents)
```

---

## 🔧 Troubleshooting

### Проблема 1: anonymousId меняется при каждом визите

**Причина:** RudderStack не сохраняет ID в cookie/localStorage

**Решение:**

```javascript
// Явно настроить storage
rudderanalytics.load(writeKey, dataPlaneUrl, {
  storage: {
    encryption: {
      version: 'v3'
    },
    type: 'localStorage', // Или 'cookie'
  },
  setCookieDomain: 'yoursite.com', // Для cross-subdomain tracking
});
```

---

### Проблема 2: UTM параметры теряются на второй странице

**Причина:** UTM только в URL первой страницы, не сохраняются

**Решение:** Использовать `saveUtmToStorage()` и `getStoredUtm()` (см. выше)

---

### Проблема 3: Конверсии не атрибутируются

**Возможные причины:**

1. **anonymousId разный в Page Viewed и Order Completed**
   - Проверить: `rudderanalytics.getAnonymousId()` в обоих событиях

2. **utm_id не передан в Page Viewed**
   - Проверить: event payload в RudderStack dashboard

3. **UserSession не создалась**
   - Проверить: `SELECT * FROM user_sessions WHERE utm_id = 'inf_test_123'`

4. **Backend не нашел UserSession**
   - Проверить logs: `/api/v1/rudderstack/track`

---

## 📊 Мониторинг

### Метрики для отслеживания

1. **Attribution Rate:**
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE traffic_source_id IS NOT NULL) * 100.0 / COUNT(*) AS attribution_rate
   FROM conversions;
   ```
   - Цель: >95%

2. **Average Time to Conversion:**
   ```sql
   SELECT AVG(time_to_conversion) / 86400 AS avg_days_to_conversion
   FROM conversions;
   ```

3. **Multi-touch Rate:**
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE touch_count > 1) * 100.0 / COUNT(*) AS multi_touch_rate
   FROM user_sessions
   WHERE EXISTS (SELECT 1 FROM conversions WHERE conversions.external_id = user_sessions.external_id);
   ```

---

## ✅ Checklist

### Frontend Setup
- [ ] RudderStack SDK установлен
- [ ] `anonymousId` сохраняется в localStorage/cookie
- [ ] UTM параметры извлекаются из URL
- [ ] UTM сохраняются в localStorage (30 дней)
- [ ] Page Viewed event отправляется с `utm_id`
- [ ] Order Completed event отправляется с `anonymousId`
- [ ] Identify вызывается после регистрации (опционально)

### Backend Setup
- [ ] Webhook `/api/v1/rudderstack/track` настроен
- [ ] UserSession создается при Page Viewed
- [ ] Conversion создается при Order Completed
- [ ] Атрибуция работает через `external_id`
- [ ] Pattern performance обновляется

### Testing
- [ ] `anonymousId` не меняется при reload
- [ ] UTM сохраняется между страницами
- [ ] E2E тест attribution проходит
- [ ] Attribution rate >95%

---

## 🎓 Best Practices

1. **Cookie Consent:**
   - Если требуется GDPR compliance, используйте cookie consent banner
   - После согласия: `rudderanalytics.load(...)`

2. **Cross-domain Tracking:**
   - Если лендинг на `landing.com`, а checkout на `app.com`:
   ```javascript
   rudderanalytics.load(writeKey, dataPlaneUrl, {
     setCookieDomain: '.yourcompany.com'
   });
   ```

3. **Server-side Tracking:**
   - Для критичных событий (Order Completed) дублируйте server-side:
   ```python
   from rudderstack.analytics import Analytics

   analytics = Analytics(write_key='...')
   analytics.track(
       user_id=user_id,
       anonymous_id=anonymous_id,
       event='Order Completed',
       properties={...}
   )
   ```

---

## 📚 Дополнительные ресурсы

- **RudderStack Docs:** https://www.rudderstack.com/docs/
- **JavaScript SDK:** https://www.rudderstack.com/docs/sources/event-streams/sdks/rudderstack-javascript-sdk/
- **Server SDK (Python):** https://www.rudderstack.com/docs/sources/event-streams/sdks/rudderstack-python-sdk/

---

**⚠️ ВАЖНО:** Без правильной настройки `external_id` attribution **не сработает**.

Потратьте время на тщательное тестирование frontend setup - это фундамент всей системы!

✅ Good luck!
