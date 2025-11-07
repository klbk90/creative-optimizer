# 🔗 UTM → Markov Chain: Полный цикл

## 📊 Как UTM данные обучают Markov Chain модель

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Креатив    │ →  │  UTM ссылка │ →  │  Микро-тест │ →  │  Обучение   │
│  + паттерны │    │  + трекинг  │    │  + данные   │    │  Markov     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🎬 ПОЛНЫЙ WORKFLOW

### Цикл 1: Первичное обучение модели (20 креативов)

#### Шаг 1: Создать 20 креативов с паттернами

```bash
POST /api/v1/creative/creatives
Authorization: Bearer YOUR_JWT_TOKEN

# Креатив 1
{
  "name": "Video 1 - Wait Hook",
  "creative_type": "ugc",
  "product_category": "lootbox",
  "video_url": "https://tiktok.com/@user/video/1",
  "production_cost": 15000,  # $150 в центах

  # Паттерны (для Markov Chain!)
  "hook_type": "wait",
  "emotion": "excitement",
  "pacing": "fast",
  "cta_type": "urgency",
  "has_text_overlay": true,
  "has_voiceover": true
}

# Response:
{
  "creative_id": "creative-uuid-1",
  "message": "Creative saved successfully"
}
```

**Повторить 20 раз** с разными паттернами:
- 5 креативов: hook=wait, emotion=excitement
- 5 креативов: hook=question, emotion=curiosity
- 5 креативов: hook=bold_claim, emotion=greed
- 5 креативов: hook=urgency, emotion=fomo

#### Шаг 2: Создать UTM ссылки для каждого креатива

```bash
POST /api/v1/utm/generate

# Для Video 1
{
  "utm_source": "tiktok",
  "utm_medium": "spark_ads",
  "utm_campaign": "test_video_1",  # ← Уникальное имя!
  "utm_content": "creative-uuid-1",  # ← ID креатива!
  "link_type": "landing"
}

# Response:
{
  "utm_id": "tiktok_abc123",
  "landing_url": "https://yourdomain.com/l/tiktok_abc123",
  "direct_url": "https://t.me/bot?start=tiktok_abc123"
}
```

**Повторить для всех 20 креативов**. Получите 20 UTM ссылок.

#### Шаг 3: Запустить микро-тесты на TikTok

**Для каждого видео:**
1. Загрузить на TikTok
2. Запустить Spark Ad
3. Бюджет: $50
4. Landing URL: `https://yourdomain.com/l/tiktok_abc123`

**Итого**: 20 × $50 = $1,000

#### Шаг 4: Подождать 3-7 дней

За это время система автоматически собирает:
- Клики через landing pages
- Конверсии через webhook
- GeoIP, device, user agent

Данные попадают в таблицу `traffic_sources`:

```sql
-- Пример данных после 3 дней
utm_id: tiktok_abc123
utm_campaign: test_video_1
utm_content: creative-uuid-1
clicks: 500
conversions: 75
revenue: 375000  # $3,750
```

#### Шаг 5: Обновить креативы из UTM данных

**Вариант A: Обновить один креатив**

```bash
POST /api/v1/creative/update-from-utm
{
  "creative_id": "creative-uuid-1",
  "utm_campaign": "test_video_1"
}

# Response:
{
  "message": "Creative performance updated from UTM data",
  "creative_id": "creative-uuid-1",
  "utm_campaign": "test_video_1",
  "metrics": {
    "impressions": 10000,
    "clicks": 500,
    "conversions": 75,
    "revenue": 3750,  # $
    "ctr": 0.05,      # 5%
    "cvr": 0.15,      # 15%
    "roas": 7.5       # 7.5x
  }
}
```

**Вариант B: Массово обновить все 20 креативов**

```bash
POST /api/v1/creative/bulk-update-from-utm
{
  "utm_campaigns": [
    "test_video_1",
    "test_video_2",
    "test_video_3",
    ...
    "test_video_20"
  ]
}

# Response:
{
  "message": "Updated 20 creatives",
  "results": [
    {
      "creative_id": "creative-uuid-1",
      "utm_campaign": "test_video_1",
      "cvr": 0.15,
      "conversions": 75
    },
    ...
  ]
}
```

#### Шаг 6: Обучить Markov Chain модель

```bash
POST /api/v1/creative/train-markov-chain
{
  "product_category": "lootbox",
  "min_sample_size": 5
}

# Response:
{
  "message": "Markov Chain model trained successfully",
  "product_category": "lootbox",
  "total_creatives": 20,
  "patterns_learned": 8,
  "patterns": [
    {
      "pattern": "wait_excitement_fast",
      "sample_size": 5,
      "avg_cvr": 0.15
    },
    {
      "pattern": "question_curiosity_medium",
      "sample_size": 5,
      "avg_cvr": 0.12
    },
    {
      "pattern": "bold_claim_greed_fast",
      "sample_size": 5,
      "avg_cvr": 0.08
    },
    ...
  ],
  "model_ready": true,
  "next_step": "Use POST /api/v1/creative/analyze to predict new creatives"
}
```

🎉 **Модель обучена!**

---

### Цикл 2: Использование модели для предсказаний

#### Шаг 7: Заказать новые UGC креативы (10 штук)

Получили 10 новых видео от Fiverr.

#### Шаг 8: Анализ + Предсказание CVR

```bash
POST /api/v1/creative/analyze
{
  "product_category": "lootbox",

  # Вариант 1: Указать паттерны вручную
  "hook_type": "wait",
  "emotion": "excitement",
  "pacing": "fast",
  "cta_type": "urgency"

  # Вариант 2: Загрузить видео для AI анализа
  # "video_url": "https://..."
}

# Response:
{
  "predicted_cvr": 0.145,  # 14.5% CVR!
  "confidence_score": 0.85,
  "sample_size": 5,
  "prediction_method": "exact_match",
  "confidence_interval": [0.08, 0.17],
  "reasoning": "Pattern 'wait_excitement_fast' historically performs well with 5 similar creatives showing 15% average CVR"
}
```

Анализируем все 10:
- Video A: CVR = 14.5% ✅ Тестировать
- Video B: CVR = 13.2% ✅ Тестировать
- Video C: CVR = 11.8% ✅ Тестировать
- Video D: CVR = 5.2% ❌ НЕ тестировать
- Video E: CVR = 4.1% ❌ НЕ тестировать
- ...

#### Шаг 9: Выбор топ-3 для масштабирования

```
Без Markov Chain:
  20 креативов × $250 (full test) = $5,000
  → 3 победителя найдено

С Markov Chain:
  10 креативов × $50 (micro test) = $500
  → Модель предсказала топ-3
  → Масштабирование топ-3 × $1,500 = $4,500
  → Итого: $5,000
  → Экономия: $4,500 на тестировании плохих креативов!
```

#### Шаг 10: Масштабирование

```bash
POST /api/v1/creative/recommend/scaling
{
  "budget": 500000,  # $5,000
  "min_cvr": 0.10
}

# Response:
{
  "recommended_creatives": [
    {
      "id": "video-a",
      "name": "Video A",
      "cvr": 0.145,
      "roas": 4.8,
      "recommended_budget": 166666,  # $1,667
      "expected_conversions": 241
    },
    ...
  ],
  "total_budget": 500000,
  "expected_revenue": 2400000,  # $24,000
  "expected_roi": 4.8,
  "confidence": 0.85
}
```

---

## 🔄 Непрерывное обучение

### После масштабирования победителей:

1. Собрать данные из масштабированных кампаний
2. Обновить креативы: `POST /update-from-utm`
3. Переобучить модель: `POST /train-markov-chain`
4. Модель становится точнее с каждым циклом!

---

## 📊 Структура данных в БД

### Таблица: `creatives`
```sql
id: uuid
hook_type: "wait"
emotion: "excitement"
pacing: "fast"
impressions: 10000
clicks: 500
conversions: 75
cvr: 1500  # 15% × 10000
```

### Таблица: `traffic_sources`
```sql
utm_id: "tiktok_abc123"
utm_campaign: "test_video_1"
utm_content: "creative-uuid-1"  # ← Связь с креативом!
clicks: 500
conversions: 75
revenue: 375000
```

### Таблица: `pattern_performance`
```sql
hook_type: "wait"
emotion: "excitement"
pacing: "fast"
sample_size: 5
total_conversions: 375
avg_cvr: 1500  # 15% × 10000
transition_probability: 1500  # P(conversion|pattern)
```

---

## 🎯 API Endpoints Summary

### 1. Создание и управление
```
POST /api/v1/creative/creatives         - Создать креатив
POST /api/v1/utm/generate               - Создать UTM ссылку
```

### 2. Сбор данных (автоматически)
```
GET  /api/v1/landing/l/{utm_id}         - Landing page (трекинг)
POST /api/v1/utm/conversion             - Webhook конверсии
```

### 3. Обновление из UTM
```
POST /api/v1/creative/update-from-utm      - Один креатив
POST /api/v1/creative/bulk-update-from-utm - Все креативы
```

### 4. Обучение Markov Chain
```
POST /api/v1/creative/train-markov-chain   - Обучить модель
```

### 5. Предсказания
```
POST /api/v1/creative/analyze              - Предсказать CVR
POST /api/v1/creative/recommend/scaling    - Рекомендации
```

### 6. Кластеризация
```
POST /api/v1/creative/cluster/visual       - Visual clustering
POST /api/v1/creative/cluster/patterns     - Pattern clustering
GET  /api/v1/creative/cluster/winning      - Найти выстреливающий кластер
```

---

## 💡 Tips & Best Practices

### 1. **Naming Convention для UTM**

```
utm_campaign = "test_{creative_name}_{date}"
utm_content = "{creative_id}"

Примеры:
- test_video_1_20250115
- test_video_waitHook_20250115
```

### 2. **Минимальный sample size**

Для надежных предсказаний:
- Minimum 5 креативов на паттерн
- Minimum 50 конверсий на паттерн

### 3. **Обновление модели**

Переобучайте модель:
- После каждых 20 новых креативов
- Или раз в 2 недели

### 4. **A/B тестирование паттернов**

Тестируйте похожие паттерны:
```
Group A: wait_excitement_fast (5 креативов)
Group B: wait_excitement_medium (5 креативов)

Результат: fast пacing выигрывает на 20%
```

---

## 🚀 Полный скрипт автоматизации

```bash
#!/bin/bash

# 1. Массовое создание креативов
for i in {1..20}; do
  curl -X POST "http://localhost:8000/api/v1/creative/creatives" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name":"Video '$i'", ...}'
done

# 2. Массовое создание UTM ссылок
for i in {1..20}; do
  curl -X POST "http://localhost:8000/api/v1/utm/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"utm_campaign":"test_video_'$i'", ...}'
done

# 3. Ждем 7 дней...

# 4. Массовое обновление
curl -X POST "http://localhost:8000/api/v1/creative/bulk-update-from-utm" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"utm_campaigns":["test_video_1", ..., "test_video_20"]}'

# 5. Обучение модели
curl -X POST "http://localhost:8000/api/v1/creative/train-markov-chain" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"product_category":"lootbox"}'

# 6. Готово!
```

---

## 📈 Результат

### Экономика:

**Цикл 1 (Обучение):**
```
UGC креативы: 20 × $150 = $3,000
Микро-тесты: 20 × $50 = $1,000
Итого: $4,000

Результат: Модель обучена
```

**Цикл 2 (Использование):**
```
UGC креативы: 10 × $150 = $1,500
Анализ через API: бесплатно
Масштабирование топ-3: $5,000
Итого: $6,500

Без модели потратили бы: $11,500
Экономия: $5,000 (43%)!
```

**ROI модели растет с каждым циклом!** 🚀

---

**Готово! Теперь у вас полная интеграция UTM → Markov Chain!** 🎉
