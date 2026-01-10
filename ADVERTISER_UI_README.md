# 🎯 Advertiser UI - Инструкция по запуску

## Что это?

**Advertiser UI** - это интерфейс для владельцев EdTech бизнеса, где они принимают решения на основе данных о тестировании креативов с микро-инфлюенсерами.

---

## 🚀 Быстрый старт

### 1️⃣ Запустить Backend (API)

```bash
cd /Users/aliakseiramanchyk/creative-optimizer

# Активировать виртуальное окружение (если есть)
source venv/bin/activate

# Запустить API
uvicorn api.main:app --reload --port 8000
```

Backend будет доступен на: **http://localhost:8000**

Проверка: **http://localhost:8000/docs** (Swagger UI)

---

### 2️⃣ Запустить Frontend (Admin Dashboard)

```bash
cd /Users/aliakseiramanchyk/creative-optimizer/frontend

# Установить зависимости (если еще не установлены)
npm install

# Запустить dev server
npm run dev
```

Frontend будет доступен на: **http://localhost:3000**

---

## 📱 Разделы Advertiser UI

### 1. **Dashboard (Overview)**
📍 http://localhost:3000/dashboard

**Что показывается:**
- 💰 Total Spend (на тесты)
- 💵 Total Revenue (с конверсий)
- 📊 Global CVR (средний по всем креативам)
- 💎 Estimated Savings (сколько сэкономили на плохих паттернах)
- 📈 График Winning vs Losing Patterns
- 🏆 Топ инфлюенсеров по ROI

**API Endpoint:**
```
GET /api/v1/analytics/dashboard
```

---

### 2. **Creative Lab**
📍 http://localhost:3000/creatives

**Что показывается:**
- 🎬 Список всех загруженных креативов
- 🏷️ AI-теги для каждого креатива:
  - **Hook Type** (например: "Question", "Before/After")
  - **Emotion** (например: "Curiosity", "Fear")
  - **Pacing** (например: "Fast", "Slow")
  - **Pain Point** (например: "No Time", "Too Expensive")
- 📊 Метрики креатива:
  - Impressions, Clicks, Conversions, CVR
  - Status: "In Progress", "Statistically Significant", "Scale Recommended"
- 📤 Drag-and-drop загрузка новых креативов

**API Endpoints:**
```
GET /api/v1/creative/list
POST /api/v1/creative/upload
GET /api/v1/creative/{creative_id}
```

---

### 3. **Pattern Discovery (Библиотека знаний)** ⭐ КИЛЛЕР-ФИЧА
📍 http://localhost:3000/patterns

**Что показывается:**
- 📊 Таблица всех найденных паттернов
  - Комбинация: Hook + Emotion + Pacing + Pain
  - **Mean CVR** (средний CVR паттерна)
  - **Confidence Interval** (95% доверительный интервал)
  - **Sample Size** (сколько креативов протестировано)
- 🎯 Thompson Sampling рекомендации
  - Какие паттерны тестить дальше
  - Баланс Exploration vs Exploitation
- 🟢 **Вердикт**: "Внедрять" (зеленый) или "Избегать" (красный)

**Пример вывода:**
```
Паттерн: Question + Curiosity + Fast + No Time
Mean CVR: 12.5% (CI: 8.7% - 17.3%)
Sample Size: 15 креативов
Вердикт: ✅ Внедрять во все новые ролики
```

**API Endpoints:**
```
GET /api/v1/rudderstack/thompson-sampling?product_category=programming
GET /api/v1/optimize/gaps/find?product_category=programming
GET /api/v1/optimize/trends/classify?hook_type=question&emotion=curiosity
```

**Байесовское обновление:**
Система автоматически обновляет CVR паттернов через RudderStack webhook:
```
POST /api/v1/rudderstack/track
```

---

### 4. **Influencer Manager**
📍 http://localhost:3000/influencers

**Что показывается:**

#### Tab 1: Search (Поиск микро-блогеров)
- 🔍 Поиск через Modash API
- Фильтры: ниша, followers, engagement rate
- Кнопка "Найти 20 микроблогеров"

#### Tab 2: Campaigns (Кампании)
- 📦 Группировка блогеров под конкретный креатив
- Статус кампании: Active, Paused, Completed
- Metrics: Total Spent, Revenue, ROI

#### Tab 3: Links (UTM ссылки)
- 🔗 Список сгенерированных UTM ссылок для каждого инфлюенсера
- Статистика по ссылке:
  - Clicks
  - Conversions
  - Revenue
  - CVR
- Формат UTM: `https://your-site.com/landing?utm_id=inf_creator_123`

**API Endpoints:**
```
POST /api/v1/utm/create-campaign
GET /api/v1/utm/links?campaign_id=xxx
GET /api/v1/analytics/influencers
```

---

## 🎯 Полный флоу (End-to-End)

### Шаг 1: Клиент загружает креативы
1. Заходит в **Creative Lab** → http://localhost:3000/creatives
2. Drag-and-drop 10 видео
3. Система автоматически анализирует:
   - Hook Type (AI Vision)
   - Emotion (AI Vision)
   - Pacing (AI Vision)
   - Pain Point (AI NLP)

### Шаг 2: Создание кампании
1. Система находит 20 микро-инфлюенсеров (через Modash API)
2. Генерирует 20 уникальных UTM ссылок
3. Формат: `https://your-site.com/landing?utm_id=inf_creator_123`

### Шаг 3: Инфлюенсер публикует пост
- Ссылка: `https://your-site.com/landing?utm_id=inf_creator_123`
- Студент кликает → попадает на **Landing Page**

### Шаг 4: Landing Page (для студентов)
📍 http://localhost:8000/api/v1/edtech/landing?utm_id=inf_test_123

- Красивый лендинг с ценой курса
- Форма checkout
- RudderStack tracking (attribution)

### Шаг 5: Студент покупает
1. RudderStack отправляет событие:
   ```json
   {
     "event": "Order Completed",
     "properties": {
       "total": 50.00,
       "utm_id": "inf_creator_123"
     }
   }
   ```

2. Backend webhook обрабатывает конверсию:
   ```
   POST /api/v1/rudderstack/track
   ```

3. Байесовское обновление паттернов:
   - Обновляет `pattern_performance` таблицу
   - Пересчитывает Mean CVR и Confidence Interval

### Шаг 6: Клиент возвращается в админку
1. Заходит в **Dashboard** → видит:
   - 15 конверсий
   - $735 revenue
   - CVR 12%

2. Заходит в **Pattern Discovery** → видит:
   ```
   Паттерн "Question + Curiosity" работает лучше всего
   CVR: 17% (CI: 12% - 23%)
   Рекомендация: Внедрять в новые креативы
   ```

3. Передает вывод видеомонтажеру:
   > "Делай больше роликов, которые начинаются с вопроса
   > и вызывают любопытство. Это принесло нам $450 из $735 revenue."

---

## 🔧 Технологии

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL** (база данных)
- **RudderStack** (attribution tracking)
- **Байесовская статистика** (Beta-распределение для CVR)
- **Thompson Sampling** (рекомендации паттернов)

### Frontend
- **React** (18+)
- **React Router** (navigation)
- **Tailwind CSS** (styling)
- **Recharts** (графики)
- **Axios** (HTTP запросы)
- **Lucide React** (иконки)

---

## 📊 API Documentation

После запуска backend, полная документация доступна:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Тестирование

### Тест 1: Создать мок-конверсию

```bash
curl -X POST http://localhost:8000/api/v1/rudderstack/track \
  -H "Content-Type: application/json" \
  -d '{
    "event": "Order Completed",
    "userId": "test_user_123",
    "properties": {
      "total": 50.00,
      "utm_id": "inf_test_123"
    }
  }'
```

### Тест 2: Получить Thompson Sampling рекомендации

```bash
curl "http://localhost:8000/api/v1/rudderstack/thompson-sampling?product_category=programming&n_recommendations=5"
```

### Тест 3: Открыть Dashboard

1. Запустить backend и frontend
2. Открыть http://localhost:3000/dashboard
3. Проверить, что данные загружаются

---

## ❓ Troubleshooting

### Проблема: Backend не запускается
**Решение:**
```bash
# Проверить PostgreSQL
docker ps | grep postgres

# Если нет - запустить:
docker-compose up -d postgres
```

### Проблема: Frontend не видит API
**Решение:**
Проверить `.env` в frontend:
```env
VITE_API_URL=http://localhost:8000
```

### Проблема: CORS ошибка
**Решение:**
Проверить `utils/security.py` на backend:
```python
def get_cors_origins():
    return [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
    ]
```

---

## 🎯 Что дальше?

1. **Интеграция Modash** - подключить реальный поиск инфлюенсеров
2. **A/B Testing** - статистическая значимость между паттернами
3. **LTV Prediction** - предсказывать lifetime value пользователей
4. **Pattern Gap Finder** - находить непротестированные комбинации

---

## 📞 Поддержка

Если что-то не работает - проверь:
1. ✅ Backend запущен (http://localhost:8000/health)
2. ✅ Frontend запущен (http://localhost:3000)
3. ✅ PostgreSQL работает
4. ✅ CORS настроен правильно

**Happy testing! 🚀**
