# Creative Optimizer MVP - Quick Start

## Запуск

```bash
./start-mvp.sh
```

## Доступ

- **UI**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## MVP Функционал

### ✅ Работает:
- Загрузка видео креативов
- Ручное указание campaign_tag (метка кампании)
- Ручное обновление метрик (impressions, clicks, conversions)
- Список креативов с фильтрацией
- Базовая аналитика

### 📊 Как использовать:

1. **Загрузить креатив:**
   - UI: http://localhost:3001/upload
   - Указать campaign_tag (например: "tiktok_jan_2025")

2. **Обновить метрики:**
   - API: PUT `/api/v1/creative/creatives/{id}/metrics`
   - Указать impressions, clicks, conversions

3. **Посмотреть результаты:**
   - UI: http://localhost:3001/creatives
   - Фильтр по campaign_tag

### ⚠️ Упрощено для MVP:
- UTM tracking отключен (вместо него campaign_tag)
- AI анализ видео отключен (нет OpenCV/librosa)
- Pattern recommendations отключены
- Manual metrics input вместо автоматического

### 🔧 Команды:

```bash
# Остановить
docker-compose down

# Логи
docker-compose logs -f api
docker-compose logs -f frontend

# Перезапуск
docker-compose restart api frontend

# Пересборка
docker-compose build api frontend
```

## Что добавить потом:

1. **Вернуть OpenCV + ffmpeg** в Dockerfile для видео анализа
2. **Включить pattern_optimization router** для ML рекомендаций
3. **Настроить UTM** для автоматического трекинга
4. **Добавить аутентификацию** (сейчас отключена)
