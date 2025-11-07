"""
Prometheus metrics для мониторинга.

Метрики:
- utm_clicks_total - Количество кликов
- utm_conversions_total - Количество конверсий
- utm_revenue_cents - Доход в центах
- creative_cvr - CVR креативов
- api_request_duration - Длительность API запросов
- api_request_total - Количество API запросов
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time


# ==================== METRICS ====================

# UTM Tracking Metrics
utm_clicks_total = Counter(
    'utm_clicks_total',
    'Total UTM clicks',
    ['utm_source', 'utm_campaign']
)

utm_conversions_total = Counter(
    'utm_conversions_total',
    'Total conversions',
    ['utm_source', 'utm_campaign']
)

utm_revenue_cents = Counter(
    'utm_revenue_cents',
    'Total revenue in cents',
    ['utm_source', 'utm_campaign']
)

# Creative Metrics
creative_cvr = Gauge(
    'creative_cvr',
    'Creative conversion rate (CVR)',
    ['creative_id', 'creative_name', 'cluster_id']
)

creative_roas = Gauge(
    'creative_roas',
    'Creative ROAS',
    ['creative_id', 'creative_name']
)

creative_impressions = Counter(
    'creative_impressions_total',
    'Total creative impressions',
    ['creative_id']
)

# Cluster Metrics
cluster_avg_cvr = Gauge(
    'cluster_avg_cvr',
    'Average CVR by cluster',
    ['cluster_id']
)

cluster_size = Gauge(
    'cluster_size',
    'Number of creatives in cluster',
    ['cluster_id']
)

# API Performance Metrics
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status_code']
)

api_request_total = Counter(
    'api_request_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

# Database Metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Redis Metrics
redis_operations = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation']  # get, set, delete
)

# Model Quality Metrics
model_accuracy = Gauge(
    'model_accuracy',
    'Model MAE (Mean Absolute Error)',
    ['model_type', 'user_id', 'product_category']
)

model_hit_rate = Gauge(
    'model_hit_rate',
    'Model hit rate (% predictions within ±20%)',
    ['model_type', 'product_category']
)

model_training_duration = Histogram(
    'model_training_duration_seconds',
    'Model training duration',
    ['model_type', 'product_category']
)

model_predictions_total = Counter(
    'model_predictions_total',
    'Total model predictions made',
    ['model_type', 'product_category']
)


# ==================== HELPERS ====================

def track_click(utm_source: str, utm_campaign: str):
    """Трекнуть клик."""
    utm_clicks_total.labels(
        utm_source=utm_source,
        utm_campaign=utm_campaign
    ).inc()


def track_conversion(utm_source: str, utm_campaign: str, amount_cents: int):
    """Трекнуть конверсию."""
    utm_conversions_total.labels(
        utm_source=utm_source,
        utm_campaign=utm_campaign
    ).inc()

    utm_revenue_cents.labels(
        utm_source=utm_source,
        utm_campaign=utm_campaign
    ).inc(amount_cents)


def track_creative_performance(creative_id: str, creative_name: str, cvr: float, roas: float, cluster_id: int = None):
    """Обновить метрики креатива."""
    creative_cvr.labels(
        creative_id=creative_id,
        creative_name=creative_name,
        cluster_id=str(cluster_id) if cluster_id is not None else "none"
    ).set(cvr)

    creative_roas.labels(
        creative_id=creative_id,
        creative_name=creative_name
    ).set(roas)


def track_cluster_metrics(cluster_id: int, avg_cvr: float, size: int):
    """Обновить метрики кластера."""
    cluster_avg_cvr.labels(cluster_id=str(cluster_id)).set(avg_cvr)
    cluster_size.labels(cluster_id=str(cluster_id)).set(size)


def track_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Трекнуть API запрос."""
    api_request_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()

    api_request_duration.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).observe(duration)


# ==================== DECORATORS ====================

def track_time(query_type: str = "unknown"):
    """Декоратор для трекинга времени выполнения."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start

            db_query_duration.labels(query_type=query_type).observe(duration)

            return result
        return wrapper
    return decorator


# ==================== METRICS ENDPOINT ====================

def get_metrics():
    """
    Получить все метрики в формате Prometheus.

    Usage в FastAPI:

    @app.get("/metrics")
    def metrics():
        return Response(
            content=get_metrics(),
            media_type=CONTENT_TYPE_LATEST
        )
    """
    return generate_latest()
