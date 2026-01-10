# 🎬 Creative Optimizer - Полный Workflow

## Шаг 0: Запуск системы

```bash
cd creative-optimizer
./setup-and-start.sh
```

Откройте браузер:
- UI: http://localhost:3001
- API Docs: http://localhost:8000/docs

---

## Сценарий: Тестируем креативы для Language Learning App

### Шаг 1: Загружаем 5 креативов с разными паттернами

```bash
# Креатив 1: "Before/After" hook + "Achievement" emotion
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video1.mp4" \
  -F "creative_name=UGC - Before After transformation" \
  -F "product_category=language_learning" \
  -F "creative_type=ugc" \
  -F "campaign_tag=batch_jan_2025" \
  -F "hook_type=before_after" \
  -F "emotion=achievement"

# Response:
# {
#   "id": "abc-123",
#   "predicted_cvr": 0.05,  ← Первый раз, система не знает → 5% default
#   "confidence": 0.1,
#   "message": "Creative uploaded! Predicted CVR: 5.0%"
# }

# Креатив 2: "Question" hook + "Curiosity" emotion
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video2.mp4" \
  -F "creative_name=UGC - Question hook" \
  -F "campaign_tag=batch_jan_2025" \
  -F "hook_type=question" \
  -F "emotion=curiosity"

# Креатив 3: "Social Proof" hook + "FOMO" emotion
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video3.mp4" \
  -F "creative_name=UGC - Social proof" \
  -F "campaign_tag=batch_jan_2025" \
  -F "hook_type=social_proof" \
  -F "emotion=fomo"

# И так далее...
```

### Шаг 2: Запускаем рекламу (TikTok / Facebook Ads)

Вы запускаете эти 5 креативов на рекламу:
- Бюджет: $50 на каждый
- Платформа: TikTok Spark Ads
- Аудитория: 18-35, интересуется языками
- Длительность: 3-7 дней

### Шаг 3: Собираем метрики после теста

Через 7 дней у вас есть результаты:

```bash
# Креатив 1 (before_after + achievement): WINNER!
curl -X PUT http://localhost:8000/api/v1/creative/creatives/abc-123/metrics \
  -F "impressions=50000" \
  -F "clicks=2500" \
  -F "conversions=400"
# CVR = 400/50000 = 0.008 (0.8%)

# Response:
# {
#   "cvr": 0.008,
#   "pattern_updated": true  ← Markov Chain обновился!
# }

# Креатив 2 (question + curiosity): OK
curl -X PUT http://localhost:8000/api/v1/creative/creatives/def-456/metrics \
  -F "impressions=48000" \
  -F "clicks=1920" \
  -F "conversions=240"
# CVR = 0.005 (0.5%)

# Креатив 3 (social_proof + fomo): LOSER
curl -X PUT http://localhost:8000/api/v1/creative/creatives/ghi-789/metrics \
  -F "impressions=52000" \
  -F "clicks=1040" \
  -F "conversions=104"
# CVR = 0.002 (0.2%)

# Креатив 4 (urgency + scarcity): OK
# CVR = 0.006 (0.6%)

# Креатив 5 (transformation + motivation): WINNER!
# CVR = 0.009 (0.9%)
```

### Шаг 4: Система ОБУЧИЛАСЬ! Смотрим что она запомнила

```bash
# Проверяем топ паттерны
curl http://localhost:8000/api/v1/creative/patterns/top?product_category=language_learning
```

**Response:**
```json
[
  {
    "hook_type": "transformation",
    "emotion": "motivation",
    "avg_cvr": 0.009,
    "sample_size": 1,
    "total_conversions": 468
  },
  {
    "hook_type": "before_after",
    "emotion": "achievement",
    "avg_cvr": 0.008,
    "sample_size": 1,
    "total_conversions": 400
  },
  {
    "hook_type": "urgency",
    "emotion": "scarcity",
    "avg_cvr": 0.006,
    "sample_size": 1,
    "total_conversions": 312
  }
]
```

### Шаг 5: Получаем ML рекомендации для следующего батча

```bash
# Thompson Sampling рекомендует что тестировать дальше
curl http://localhost:8000/api/v1/creative/patterns/recommend?product_category=language_learning&n_patterns=5
```

**Response:**
```json
[
  {
    "hook_type": "transformation",
    "emotion": "motivation",
    "expected_cvr": 0.009,
    "confidence": 0.05,  ← Мало данных (1 тест)
    "sample_size": 1,
    "priority": 0.89,
    "reasoning": "New pattern, high exploration value"
  },
  {
    "hook_type": "before_after",
    "emotion": "achievement",
    "expected_cvr": 0.008,
    "confidence": 0.05,
    "sample_size": 1,
    "priority": 0.88,
    "reasoning": "New pattern, high exploration value"
  }
]
```

**Система рекомендует:**
✅ Протестировать еще "transformation + motivation" (показал 0.9%)
✅ Протестировать еще "before_after + achievement" (показал 0.8%)
❌ НЕ тестировать "social_proof + fomo" (показал только 0.2%)

---

## Шаг 6: Второй батч (система УЖЕ УМНЕЕ!)

Заказываем еще 20 креативов, но теперь используем ЗНАНИЯ системы:

```bash
# Креатив 6: Снова "transformation + motivation" (proven winner)
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video6.mp4" \
  -F "creative_name=UGC - Transformation v2" \
  -F "campaign_tag=batch_feb_2025" \
  -F "hook_type=transformation" \
  -F "emotion=motivation"

# Response:
# {
#   "predicted_cvr": 0.009,  ← УЖЕ НЕ 5%! Система ЗНАЕТ этот паттерн!
#   "confidence": 0.05,
#   "message": "Creative uploaded! Predicted CVR: 0.9%"
# }

# Креатив 7: Новый паттерн "pain_point + frustration"
curl -X POST http://localhost:8000/api/v1/creative/upload \
  -F "video=@video7.mp4" \
  -F "hook_type=pain_point" \
  -F "emotion=frustration"

# Response:
# {
#   "predicted_cvr": 0.05,  ← Новый паттерн → дефолт 5%
#   "confidence": 0.1
# }
```

---

## Через 3 месяца (после 100+ тестов):

### Markov Chain знает ВСЕ паттерны:

```json
{
  "transformation + motivation": {
    "avg_cvr": 0.0085,
    "sample_size": 15,
    "confidence": 0.75  ← Высокая уверенность!
  },
  "before_after + achievement": {
    "avg_cvr": 0.0078,
    "sample_size": 18,
    "confidence": 0.90
  },
  "question + curiosity": {
    "avg_cvr": 0.0051,
    "sample_size": 12,
    "confidence": 0.60
  },
  "social_proof + fomo": {
    "avg_cvr": 0.0023,
    "sample_size": 8,
    "confidence": 0.40
  }
}
```

### Thompson Sampling теперь ОЧЕНЬ умный:

```json
{
  "recommendations": [
    {
      "hook_type": "before_after",
      "emotion": "achievement",
      "expected_cvr": 0.0078,
      "sample_size": 18,
      "priority": 0.95,
      "reasoning": "Proven winner with 18 tests"  ← EXPLOITATION
    },
    {
      "hook_type": "storytelling",
      "emotion": "inspiration",
      "expected_cvr": 0.05,
      "sample_size": 0,
      "priority": 0.52,
      "reasoning": "Untested pattern, worth exploring"  ← EXPLORATION
    }
  ]
}
```

---

## 💡 Ключевая идея:

### БЕЗ Creative Optimizer:
```
Batch 1: Тестируешь 20 креативов вслепую
  → 2-3 winners (10-15% success rate)
  → Не понимаешь ПОЧЕМУ они сработали

Batch 2: Снова тестируешь вслепую
  → Снова 10-15% success rate
  → Тратишь время и деньги на losers
```

### С Creative Optimizer:
```
Batch 1: Тестируешь 20 креативов
  → Система ЗАПОМИНАЕТ паттерны
  → 2-3 winners (10-15%)

Batch 2: Система ЗНАЕТ что работает
  → Фокусируешься на proven winners
  → 6-8 winners (30-40% success rate!)  ← В 3 РАЗА ЛУЧШЕ!

Batch 3+: Система становится еще умнее
  → Success rate растет до 50%+
```

---

## 🎯 Практический результат:

**Экономия бюджета:**
- Раньше: 20 креативов × $50 = $1,000
- Теперь: 12 "proven" × $50 + 8 "exploration" × $20 = $760
- **Сэкономил: $240 на батч**

**Рост конверсий:**
- Раньше: 10-15% success rate
- Теперь: 30-40% success rate
- **В 3 раза больше winners!**

---

## 🚀 Начни прямо сейчас:

```bash
# 1. Запусти систему
./setup-and-start.sh

# 2. Загрузи креативы
# UI: http://localhost:3001/upload
# или через API

# 3. Собери метрики после тестов

# 4. Получи рекомендации
# UI: http://localhost:3001/patterns

# 5. Повторяй и наблюдай как система становится умнее!
```
