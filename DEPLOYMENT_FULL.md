# 🚀 Full Deployment Guide - UTM Tracking с Кластеризацией

## 📋 Содержание

1. [Подготовка сервера](#подготовка-сервера)
2. [Установка зависимостей](#установка-зависимостей)
3. [Настройка окружения](#настройка-окружения)
4. [Запуск через Docker Compose](#запуск-через-docker-compose)
5. [Настройка Grafana](#настройка-grafana)
6. [Настройка доменов](#настройка-доменов)
7. [Мониторинг и алерты](#мониторинг-и-алерты)
8. [Backup и восстановление](#backup-и-восстановление)

---

## 🖥️ Подготовка сервера

### Минимальные требования:

```
CPU: 2 cores
RAM: 4 GB (8 GB recommended)
Disk: 50 GB SSD
OS: Ubuntu 20.04/22.04 LTS
```

### 1. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker --version
```

### 3. Установка Docker Compose

```bash
sudo apt install docker-compose -y
docker-compose --version
```

---

## 📦 Установка проекта

### 1. Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/your-username/utm-tracking.git
cd utm-tracking
sudo chown -R $USER:$USER .
```

### 2. Настройка окружения

```bash
# Создать .env из примера
cp .env.example .env

# Отредактировать
nano .env
```

### Минимальные переменные для production:

```bash
# Database
DATABASE_URL=postgresql://utm_user:STRONG_PASSWORD_HERE@localhost:5432/utm_tracking

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (ВАЖНО: сгенерировать новый!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Landing Pages
LANDING_BASE_URL=https://yourdomain.com/api/v1/landing/l

# Telegram Bot
ADMIN_BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789

# AI (опционально)
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Создать директорию для мониторинга

```bash
mkdir -p monitoring
```

---

## 🐳 Запуск через Docker Compose

### 1. Запуск всех сервисов

```bash
docker-compose up -d
```

Это запустит:
- ✅ PostgreSQL (порт 5432)
- ✅ Redis (порт 6379)
- ✅ API (порт 8000)
- ✅ Admin Bot
- ✅ Prometheus (порт 9090)
- ✅ Grafana (порт 3000)

### 2. Проверка статуса

```bash
docker-compose ps
```

Все контейнеры должны быть в статусе `Up`.

### 3. Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Только API
docker-compose logs -f api

# Только Grafana
docker-compose logs -f grafana
```

### 4. Применить миграции БД

```bash
docker-compose exec api alembic upgrade head
```

---

## 📊 Настройка Grafana

### 1. Открыть Grafana

```
http://your-server-ip:3000
```

**Логин**: `admin`
**Пароль**: `admin` (измените при первом входе!)

### 2. Добавить Prometheus как Data Source

1. Sidebar → Configuration → Data Sources
2. Add data source → Prometheus
3. URL: `http://prometheus:9090`
4. Save & Test

### 3. Импортировать Dashboard

Dashboard уже есть в `/monitoring/grafana-dashboard.json`.

Или вручную:
1. Sidebar → Create → Import
2. Upload JSON file: `monitoring/grafana-dashboard.json`
3. Select Prometheus data source
4. Import

### 4. Dashboard панели:

- **Total Clicks** - График кликов по кампаниям
- **Total Conversions** - График конверсий
- **Revenue** - Доход в $
- **CVR by Campaign** - Conversion rate
- **Creative CVR by Cluster** - Производительность кластеров
- **Cluster Size** - Размеры кластеров
- **API Latency** - Задержка API (p95)
- **API Requests/sec** - RPS
- **Top Performing Creatives** - Таблица топ креативов
- **Single Stats** - Общая статистика (revenue, conversions, clicks, CVR)

---

## 🌍 Настройка доменов (Production)

### 1. DNS настройка

Добавить A-записи:

```
api.yourdomain.com    → YOUR_SERVER_IP
grafana.yourdomain.com → YOUR_SERVER_IP
*.yourdomain.com      → YOUR_SERVER_IP (для landing pages)
```

### 2. Установка Nginx

```bash
sudo apt install nginx -y
```

### 3. Конфигурация Nginx для API

```bash
sudo nano /etc/nginx/sites-available/utm-api
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        deny all;  # Защита метрик
    }
}
```

### 4. Конфигурация Nginx для Grafana

```bash
sudo nano /etc/nginx/sites-available/utm-grafana
```

```nginx
server {
    listen 80;
    server_name grafana.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Активация конфигов

```bash
sudo ln -s /etc/nginx/sites-available/utm-api /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/utm-grafana /etc/nginx/sites-enabled/

# Проверка
sudo nginx -t

# Перезагрузка
sudo systemctl reload nginx
```

### 6. Установка SSL (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификатов
sudo certbot --nginx -d api.yourdomain.com
sudo certbot --nginx -d grafana.yourdomain.com

# Auto-renewal (уже настроен)
sudo certbot renew --dry-run
```

---

## ⚙️ Workflow: Микро-тесты → Кластеризация → Scaling

### 1. Загрузить креативы (20 UGC видео)

```bash
POST /api/v1/creative/save
{
  "name": "Video 1",
  "video_url": "https://...",
  "product_category": "lootbox"
}
```

Повторить 20 раз.

### 2. Микро-тесты ($50 каждый)

Запустить TikTok Spark Ads на каждый креатив с бюджетом $50.

Через 3-7 дней:

### 3. Обновить метрики

```bash
POST /api/v1/creative/update-performance
{
  "creative_id": "uuid",
  "impressions": 10000,
  "clicks": 500,
  "conversions": 75,
  "spend": 5000  # $50 в центах
}
```

### 4. Кластеризация

```bash
POST /api/v1/creative/cluster/visual?n_clusters=5
```

Ответ:
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "size": 8,
      "avg_cvr": 0.15,  // 15% CVR!
      "avg_roas": 4.2,
      "top_creative_ids": ["uuid1", "uuid2", ...]
    },
    {
      "cluster_id": 1,
      "size": 7,
      "avg_cvr": 0.08,  // 8% CVR
      ...
    }
  ]
}
```

### 5. Найти выстреливающий кластер

```bash
GET /api/v1/creative/cluster/winning?min_cvr=0.10
```

Вернет кластер с CVR > 10%.

### 6. Получить рекомендации для scaling

```bash
POST /api/v1/creative/recommend/scaling
{
  "budget": 500000,  // $5,000
  "min_cvr": 0.10
}
```

Ответ:
```json
{
  "recommended_creatives": [
    {
      "id": "uuid",
      "name": "Video 3",
      "cvr": 0.15,
      "roas": 4.2,
      "recommended_budget": 100000,  // $1,000
      "expected_conversions": 150
    },
    ...
  ],
  "total_budget": 500000,
  "expected_revenue": 2100000,  // $21,000
  "expected_roi": 4.2,
  "confidence": 0.85
}
```

### 7. Масштабирование

Залить по $1,000 на каждый рекомендованный креатив из топ-5.

### 8. Мониторинг в Grafana

Открыть Grafana dashboard:
- Отслеживать CVR by Cluster
- Revenue by Campaign
- Top Performing Creatives

---

## 📈 Мониторинг и Алерты

### Prometheus Metrics

```
http://your-server:9090
```

Доступные метрики:
```
utm_clicks_total
utm_conversions_total
utm_revenue_cents
creative_cvr
creative_roas
cluster_avg_cvr
cluster_size
api_request_duration_seconds
api_request_total
```

### Настройка алертов (Alertmanager)

TODO: Добавить Alertmanager для уведомлений:
- CVR упал ниже порога
- Revenue остановился
- API latency выше 2s
- Ошибки 5xx

---

## 💾 Backup и Восстановление

### Backup PostgreSQL

```bash
# Ручной backup
docker-compose exec postgres pg_dump -U utm_user utm_tracking > backup_$(date +%Y%m%d).sql

# Автоматический backup (cron)
crontab -e

# Добавить:
0 3 * * * cd /opt/utm-tracking && docker-compose exec postgres pg_dump -U utm_user utm_tracking > /backups/utm_$(date +\%Y\%m\%d).sql
```

### Восстановление

```bash
# Восстановить из backup
docker-compose exec -T postgres psql -U utm_user utm_tracking < backup_20250115.sql
```

### Backup Grafana dashboards

```bash
# Export dashboard
curl -X GET http://localhost:3000/api/dashboards/uid/XXX > dashboard_backup.json

# Restore
curl -X POST -H "Content-Type: application/json" \
  -d @dashboard_backup.json \
  http://localhost:3000/api/dashboards/db
```

---

## 🔒 Security Checklist

- [ ] Изменить пароли БД (не utm_password!)
- [ ] Изменить JWT_SECRET_KEY
- [ ] Изменить Grafana admin пароль
- [ ] Настроить firewall (ufw)
- [ ] Ограничить доступ к /metrics (только Prometheus)
- [ ] Включить HTTPS (Let's Encrypt)
- [ ] Backup .env файл в безопасное место
- [ ] Настроить fail2ban
- [ ] Регулярные обновления безопасности

---

## 🚦 Проверка работоспособности

### 1. Health Check API

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "services": {
    "database": "up",
    "redis": "up",
    "queue": "up"
  }
}
```

### 2. Проверка метрик

```bash
curl http://localhost:8000/metrics
```

Должен вернуть Prometheus метрики.

### 3. Проверка Grafana

```bash
curl http://localhost:3000/api/health
```

---

## 🆘 Troubleshooting

### API не запускается

```bash
# Проверить логи
docker-compose logs api

# Проверить БД
docker-compose exec postgres psql -U utm_user -d utm_tracking -c "SELECT version();"
```

### Grafana не показывает данные

1. Проверить data source: Settings → Data Sources → Prometheus → Test
2. Проверить метрики: `http://localhost:9090/targets` (все должны быть UP)
3. Перезапустить Grafana: `docker-compose restart grafana`

### Нет метрик в Prometheus

1. Проверить `/metrics` endpoint: `curl http://localhost:8000/metrics`
2. Проверить prometheus.yml конфиг
3. Перезапустить Prometheus: `docker-compose restart prometheus`

---

## 📊 Пример полного цикла

```
День 1: Заказ 20 UGC креативов ($3,000)
День 7: Получение креативов
День 8: Загрузка в систему + микро-тесты ($1,000)
День 11-15: Сбор данных
День 15: Кластеризация + выбор топ-5
День 16: Scaling $5,000 на топ-5
День 23: Анализ результатов
День 24: Масштабирование победителя до $50k/мес

ROI: $150k revenue - $59k spend = $91k profit 🚀
```

---

**Готово! Система запущена.**

Откройте:
- API Docs: `http://your-domain:8000/docs`
- Grafana: `http://your-domain:3000`
- Prometheus: `http://your-domain:9090`

Удачи в арбитраже! 💰
