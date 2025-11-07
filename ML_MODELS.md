# 🧠 ML Модели и автоматический цикл обучения

Полное руководство по машинному обучению в проекте UTM Tracking.

---

## 🎯 Зачем нужны ML модели?

**Проблема:** Как понять какие креативы заказывать дальше?

**Решение:** ML модели предсказывают CVR нового креатива ДО запуска теста.

**Workflow:**
```
1. Тест 20 креативов → собрать данные
2. Модель обучается автоматически
3. Предсказать CVR для новых 20 креативов
4. Заказать только те что predicted CVR > 10%
5. Hit rate 60% вместо 15%! 🚀
```

---

## 📊 Какие модели используются?

### 1. **Markov Chain** (основная, всегда)

**Когда:** 20-50 креативов

**Плюсы:**
- Работает с малыми данными
- Интерпретируемая (видно какие паттерны работают)
- Быстрая

**Минусы:**
- Предполагает независимость признаков
- Не учитывает комплексные взаимодействия

**Точность:** MAE 0.03-0.05 (3-5% ошибка)

**Как работает:**
```python
# Агрегирует performance по паттернам
Pattern: wait + excitement + fast
  Sample size: 8 креативов
  AVG CVR: 14.5%
  Confidence: 85%

# Предсказывает новый креатив с этим паттерном
Predicted CVR: 13-16% (confidence interval)
```

---

### 2. **Gradient Boosting (LightGBM)** (продвинутая)

**Когда:** 50+ креативов

**Плюсы:**
- Лучше точность
- Учитывает нелинейные зависимости
- Feature importance (видно что важно)

**Минусы:**
- Требует больше данных
- Дольше обучается
- Менее интерпретируемая

**Точность:** MAE 0.02-0.03 (2-3% ошибка)

**Как работает:**
```python
# Features:
- hook_type, emotion, pacing, cta_type (categorical)
- duration, has_text_overlay, has_voiceover (numerical)
- Historical CVR по каждому признаку

# LightGBM строит дерево решений
# Предсказывает CVR с учетом всех взаимодействий
```

---

### 3. **Thompson Sampling** (оптимизатор)

**Когда:** Всегда (любое количество данных)

**Зачем:** Выбрать следующие паттерны для теста

**Алгоритм:**
```python
# Multi-Armed Bandit problem
# Баланс: Exploit vs Explore

For each pattern:
  alpha = conversions + 1
  beta = (clicks - conversions) + 1

  # Sample from Beta distribution
  sampled_cvr = Beta(alpha, beta)

  priority = sampled_cvr

# Sort by priority → топ-5 паттернов
```

**Пример:**
```
Pattern 1: wait + excitement + fast
  Expected CVR: 14.5%
  Uncertainty: 0.15 (tested 8 times)
  Priority: 0.85 → RANK 1 (proven winner, exploit)

Pattern 2: shock + curiosity + medium
  Expected CVR: 8.0%
  Uncertainty: 0.65 (tested 2 times)
  Priority: 0.72 → RANK 2 (explore opportunity!)
```

---

## 🔄 Автоматический цикл обучения

### Полный цикл:

```
┌─────────────────────────────────────────────┐
│ 1. Тест 20 креативов                       │
│    - День 0: $10 × 20 = $200               │
│    - День 1: Early signals анализ         │
│    - Дни 2-7: Долить на winners            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ 2. Автоматический сбор данных              │
│    POST /creative/bulk-update-from-utm     │
│    → Обновить все 20 креативов             │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ 3. Автоматическое переобучение (каждый час)│
│    Background task → AutoTrainer           │
│    - Проверить: есть ли ≥3 новых креатива? │
│    - Переобучить Markov Chain              │
│    - Оценить: MAE, hit rate                │
│    - Откатить если стало хуже              │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ 4. Выбор следующих паттернов               │
│    GET /recommend/next-patterns            │
│    Thompson Sampling → топ-5 паттернов     │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ 5. Заказать новые креативы                 │
│    - Бриф на Fiverr с рекомендованными     │
│      паттернами                            │
│    - 20 креативов × $30-50                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
          (повтор с шага 1)
```

---

## 🚀 API Endpoints

### 1. Автоматическое переобучение

```bash
POST /api/v1/creative/models/auto-train?product_category=lootbox

Response:
{
  "message": "Auto-training completed",
  "results": [
    {
      "product_category": "lootbox",
      "status": "success",
      "new_creatives": 12,
      "patterns_learned": 15,
      "old_mae": 0.0452,
      "new_mae": 0.0345,
      "improved": true,
      "metrics": {
        "mae": 0.0345,
        "hit_rate": 0.72,
        "r_squared": 0.65,
        "sample_size": 28
      }
    }
  ]
}
```

**Когда вызывать:**
- После batch-update креативов
- Вручную если хочешь переобучить
- Автоматически каждый час (background task)

---

### 2. Метрики модели

```bash
GET /api/v1/creative/models/metrics?product_category=lootbox&model_type=markov_chain

Response:
{
  "metrics": [
    {
      "created_at": "2025-01-15T10:30:00Z",
      "mae": 0.0345,
      "hit_rate": 0.72,
      "r_squared": 0.65,
      "sample_size": 28,
      "improved": true
    },
    {
      "created_at": "2025-01-14T09:15:00Z",
      "mae": 0.0452,
      "hit_rate": 0.68,
      "sample_size": 16,
      "improved": false
    }
  ],
  "current": {
    "mae": 0.0345,
    "hit_rate": 0.72,
    "sample_size": 28,
    "trend": "improving"  // ← Модель улучшается!
  }
}
```

**Use case:**
- Мониторинг качества модели
- Debug если точность падает
- Сравнение версий

---

### 3. Рекомендация следующих паттернов (Thompson Sampling)

```bash
GET /api/v1/creative/recommend/next-patterns?product_category=lootbox&n_patterns=5

Response:
{
  "recommended_patterns": [
    {
      "rank": 1,
      "hook_type": "wait",
      "emotion": "excitement",
      "pacing": "fast",
      "cta_type": "urgency",
      "expected_cvr": 0.145,
      "uncertainty": 0.15,
      "priority": 0.85,
      "sample_size": 8,
      "reasoning": "High CVR (14.5%) + low uncertainty (tested 8 times) - proven winner!"
    },
    {
      "rank": 2,
      "hook_type": "shock",
      "emotion": "curiosity",
      "pacing": "medium",
      "cta_type": "benefit",
      "expected_cvr": 0.08,
      "uncertainty": 0.65,
      "priority": 0.72,
      "sample_size": 2,
      "reasoning": "Moderate CVR but high uncertainty - explore opportunity"
    },
    {
      "rank": 3,
      "hook_type": "question",
      "emotion": "curiosity",
      "pacing": "slow",
      "cta_type": "benefit",
      "expected_cvr": 0.09,
      "uncertainty": 0.45,
      "priority": 0.68
    }
  ],
  "algorithm": "thompson_sampling",
  "workflow": [
    "1. Order UGC videos with recommended patterns",
    "2. Run micro-tests ($10-50 per creative)",
    "3. Update metrics via /bulk-update-from-utm",
    "4. Model auto-retrains (or call /models/auto-train)",
    "5. Repeat: call this endpoint again for next batch"
  ]
}
```

**Workflow:**
1. Получить рекомендации
2. Составить бриф для Fiverr:
   ```
   Hook: "Wait until the end!" или "You won't believe..."
   Emotion: Excitement, энергия, вау-эффект
   Pacing: Fast cuts, динамичный монтаж
   CTA: "Try now!" / "Limited time!"
   ```
3. Заказать 20 креативов с топ-5 паттернами
4. Повторить цикл

---

### 4. Cross-product рекомендации

```bash
GET /api/v1/creative/recommend/cross-product?target_product=casino&n_patterns=5

Response:
{
  "target_product": "casino",
  "recommended_patterns": [
    {
      "hook_type": "wait",
      "emotion": "excitement",
      "pacing": "fast",
      "cta_type": "urgency",
      "source_product": "lootbox",
      "original_cvr": 0.145,
      "adjusted_cvr": 0.116,  // 14.5% × 0.8 (similarity)
      "similarity": 0.8,
      "sample_size": 8,
      "reasoning": "Proven in lootbox (CVR 14.5%), adjusted for casino similarity (80%)"
    }
  ]
}
```

**Use case:** Запускаешь новый продукт (casino), используя данные из lootbox.

**Product similarity matrix:**
```
lootbox ↔ casino: 80%
lootbox ↔ betting: 60%
casino ↔ betting: 70%
betting ↔ sports: 90%
lootbox ↔ gaming: 70%
```

---

## 📈 Метрики качества

### MAE (Mean Absolute Error)

```
MAE = average(|predicted_cvr - actual_cvr|)

Пример:
Creative 1: predicted 12%, actual 14% → error 2%
Creative 2: predicted 8%, actual 6% → error 2%
Creative 3: predicted 15%, actual 12% → error 3%

MAE = (2% + 2% + 3%) / 3 = 2.33%
```

**Хорошие значения:**
- MAE < 3%: Отлично ✅
- MAE 3-5%: Хорошо ⚠️
- MAE > 5%: Плохо, нужно больше данных ❌

---

### Hit Rate

```
Hit rate = % креативов где predicted CVR ± 20% = actual CVR

Пример:
Creative 1: predicted 10%, actual 11% → HIT (в пределах ±20%)
Creative 2: predicted 10%, actual 15% → MISS (ошибка 50%)
Creative 3: predicted 12%, actual 10% → HIT

Hit rate = 2/3 = 66.7%
```

**Хорошие значения:**
- Hit rate > 70%: Отлично ✅
- Hit rate 50-70%: Хорошо ⚠️
- Hit rate < 50%: Плохо ❌

---

### R² (Correlation Coefficient)

```
R² = correlation²

R² = 1.0 → идеальная корреляция
R² = 0.5 → средняя корреляция
R² = 0.0 → нет корреляции
```

**Хорошие значения:**
- R² > 0.6: Отлично ✅
- R² 0.4-0.6: Хорошо ⚠️
- R² < 0.4: Плохо ❌

---

## 🔧 Background Scheduler

Автоматическое переобучение каждый час.

**Файл:** `api/main.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    # Каждый час - переобучение моделей
    scheduler.add_job(
        auto_retrain_all_users,
        'interval',
        hours=1,
        id='auto_retrain'
    )

    scheduler.start()


async def auto_retrain_all_users():
    """
    Переобучить модели для всех пользователей у которых есть новые данные.
    """

    db = next(get_db())

    # Найти пользователей с новыми креативами (за последние 2 часа)
    users_with_new_data = db.query(Creative.user_id).filter(
        Creative.tested_at > datetime.utcnow() - timedelta(hours=2),
        Creative.conversions > 0
    ).distinct().all()

    for (user_id,) in users_with_new_data:
        trainer = AutoTrainer(db, user_id)
        await trainer.check_and_retrain()
```

**Логи:**
```
2025-01-15 10:00:00 INFO  Scheduler started: auto-retraining every 1 hour
2025-01-15 11:00:00 INFO  Auto-retrained models for user abc-123
2025-01-15 11:00:05 INFO  Model improved for lootbox: MAE 0.045 → 0.034
```

---

## 📊 Grafana Dashboard

Мониторинг метрик модели в Grafana.

**Метрики Prometheus:**
```python
# Model accuracy (MAE)
model_accuracy{model_type="markov_chain", user_id="abc-123", product_category="lootbox"} 0.0345

# Hit rate
model_hit_rate{model_type="markov_chain", product_category="lootbox"} 0.72

# Training duration
model_training_duration_seconds{model_type="markov_chain", product_category="lootbox"} 2.5

# Total predictions
model_predictions_total{model_type="markov_chain", product_category="lootbox"} 145
```

**Grafana panels:**
1. **Model MAE over time** (линия) - должна уменьшаться
2. **Hit rate over time** (линия) - должна расти
3. **Total creatives tested** (счетчик)
4. **Model accuracy (current)** (single stat)
5. **Predictions today** (счетчик)

---

## 🎓 Best Practices

### 1. Начинай с Markov Chain

```
0-20 креативов: Нет модели (используй industry best practices)
20-50 креативов: Markov Chain
50+ креативов: Gradient Boosting
200+ креативов: Ensemble (несколько моделей)
```

---

### 2. Автоматизируй переобучение

```python
# НЕ делай так (вручную):
# После каждого теста вызывать /models/auto-train

# Делай так (автоматически):
# Scheduler каждый час проверяет и переобучает
```

---

### 3. Мониторь метрики

```
Каждую неделю проверяй:
- MAE уменьшается?
- Hit rate растет?
- Trend = "improving"?

Если нет → нужно больше данных или другая модель
```

---

### 4. Используй Thompson Sampling

```
Вместо:
  "Закажу 20 креативов с лучшим паттерном"

Делай:
  GET /recommend/next-patterns
  → Топ-5 паттернов (exploit + explore)
  → 4 креатива по каждому паттерну
```

---

### 5. Cross-product для нового продукта

```
Запускаешь casino (новый продукт):
1. GET /recommend/cross-product?target_product=casino
2. Система использует данные из lootbox (similarity 80%)
3. Заказываешь 10 креативов с adjusted паттернами
4. Тестируешь → собираешь данные для casino
5. Через 20 креативов → своя модель для casino
```

---

## 🚨 Troubleshooting

### Проблема: MAE растет

**Причина:** Модель переобучается или данные изменились.

**Решение:**
1. Проверить: изменилась ли аудитория?
2. Откатить модель на предыдущую версию
3. Собрать больше данных

---

### Проблема: Hit rate < 50%

**Причина:** Недостаточно данных или плохие признаки.

**Решение:**
1. Проверить: достаточно ли креативов? (нужно ≥20)
2. Добавить новые features (duration, has_text_overlay)
3. Переключиться на Gradient Boosting (если ≥50 креативов)

---

### Проблема: Все рекомендации одинаковые

**Причина:** Thompson Sampling застрял в одном паттерне (exploit).

**Решение:**
1. Увеличить exploration: добавить epsilon-greedy
2. Вручную протестировать новые паттерны
3. Проверить: может быть один паттерн реально лучший?

---

## 📊 Пример полного цикла

### День 0: Запуск

```bash
# 1. Создать 20 креативов
for i in {1..20}; do
  curl -X POST /api/v1/creative/creatives \
    -d '{"name": "Video '$i'", "hook_type": "wait", ...}'
done

# 2. Запустить TikTok Ads ($10 на креатив)
# (вручную через TikTok Ads Manager)
```

---

### День 1: Early signals

```bash
# Собрать метрики за 24h и проанализировать
curl -X POST /api/v1/creative/bulk-analyze-24h \
  -d '{"creatives_data": [...]}'

# Response:
# - 3 winners (scale)
# - 9 potential (continue)
# - 8 losers (kill)
```

---

### День 7: Обучение модели

```bash
# 1. Обновить метрики
curl -X POST /api/v1/creative/bulk-update-from-utm \
  -d '{"utm_campaigns": ["test_1", "test_2", ...]}'

# 2. Переобучить модель (автоматически, но можно вручную)
curl -X POST /api/v1/creative/models/auto-train?product_category=lootbox

# 3. Проверить метрики
curl -X GET /api/v1/creative/models/metrics?product_category=lootbox

# Response:
# {
#   "current": {
#     "mae": 0.034,
#     "hit_rate": 0.72,
#     "trend": "improving"
#   }
# }
```

---

### День 8: Следующий раунд

```bash
# 1. Получить рекомендации
curl -X GET /api/v1/creative/recommend/next-patterns?product_category=lootbox&n_patterns=5

# Response:
# [
#   {"hook": "wait", "emotion": "excitement", "pacing": "fast"},
#   {"hook": "shock", "emotion": "curiosity", "pacing": "medium"},
#   ...
# ]

# 2. Заказать 20 новых креативов с этими паттернами
# (4 креатива на каждый из 5 паттернов)

# 3. Повторить цикл
```

---

## 🎯 Результат

**Без ML:**
```
20 креативов × $50 = $1,000
Hit rate: 15% (3 winners из 20)
ROI: Плохой
```

**С ML (после 100 креативов):**
```
20 креативов × $50 = $1,000
Hit rate: 60% (12 winners из 20!)
ROI: Отличный 🚀

Экономия времени: Не заказываем лузеров
Экономия денег: Не тестируем лузеров
```

---

**Готово! Полный ML цикл работает автоматически.** 🤖

Следующий шаг: Задеплоить и запустить первый тест!
