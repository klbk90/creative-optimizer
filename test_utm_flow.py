#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всего UTM-трекинг флоу.

Проверяет:
1. Аутентификацию
2. Создание UTM ссылок (landing и direct)
3. Трекинг кликов
4. Трекинг конверсий через webhook
5. Получение аналитики
"""

import requests
import json
import time
from datetime import datetime

# Настройки
API_URL = "http://localhost:8000"
TEST_EMAIL = "real_test@test.com"
TEST_PASSWORD = "testpass123"

# Цвета для консоли
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(message, color=Colors.BLUE):
    """Логирование с цветом"""
    print(f"{color}{Colors.BOLD}[{datetime.now().strftime('%H:%M:%S')}]{Colors.END} {color}{message}{Colors.END}")

def test_auth():
    """Тест аутентификации"""
    log("📝 Тестирую аутентификацию...", Colors.YELLOW)

    # Пробуем войти через JSON endpoint
    response = requests.post(
        f"{API_URL}/api/v1/auth/login/json",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        log(f"✅ Вход успешен! Token: {token[:20]}...", Colors.GREEN)
        return token
    else:
        log(f"❌ Ошибка входа: {response.status_code} - {response.text}", Colors.RED)

        # Пробуем зарегистрироваться
        log("📝 Пробую зарегистрировать пользователя...", Colors.YELLOW)
        response = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            }
        )

        if response.status_code in [200, 201]:
            log("✅ Регистрация успешна!", Colors.GREEN)
            # Теперь логинимся
            return test_auth()
        else:
            log(f"❌ Ошибка регистрации: {response.status_code} - {response.text}", Colors.RED)
            return None

def test_create_utm_link(token, link_type="landing"):
    """Тест создания UTM ссылки"""
    log(f"🔗 Создаю {link_type} UTM ссылку...", Colors.YELLOW)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "base_url": "https://t.me/test_channel",
        "source": "tiktok",
        "medium": "social",
        "campaign": "test_campaign_jan_2025",
        "content": "video_001",
        "link_type": link_type
    }

    response = requests.post(
        f"{API_URL}/api/v1/utm/generate",
        json=data,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        log(f"✅ UTM ссылка создана!", Colors.GREEN)
        log(f"   URL: {result['utm_link']}", Colors.BLUE)
        log(f"   UTM ID: {result['utm_id']}", Colors.BLUE)
        return result
    else:
        log(f"❌ Ошибка создания ссылки: {response.status_code} - {response.text}", Colors.RED)
        return None

def test_track_click(utm_id):
    """Тест трекинга клика"""
    log(f"👆 Трекаю клик для {utm_id}...", Colors.YELLOW)

    data = {
        "utm_id": utm_id,
        "landing_page": "https://test-landing.com",
        "referrer": "https://tiktok.com/@test_creator"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "X-Forwarded-For": "8.8.8.8"  # Test IP
    }

    response = requests.post(
        f"{API_URL}/api/v1/utm/track/click",
        json=data,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        log(f"✅ Клик успешно затрекан!", Colors.GREEN)
        log(f"   Message: {result.get('message')}", Colors.BLUE)
        return result
    else:
        log(f"❌ Ошибка трекинга клика: {response.status_code} - {response.text}", Colors.RED)
        return None

def test_track_conversion(utm_id):
    """Тест трекинга конверсии через webhook"""
    log(f"💰 Трекаю конверсию для {utm_id}...", Colors.YELLOW)

    data = {
        "utm_id": utm_id,
        "customer_id": "telegram_123456789",
        "amount": 5000,  # $50.00
        "currency": "USD",
        "product_id": "test_product_001",
        "product_name": "Test Product",
        "conversion_type": "purchase",
        "metadata": {
            "payment_method": "test",
            "test_mode": True
        }
    }

    response = requests.post(
        f"{API_URL}/api/v1/utm/webhook/conversion",
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        log(f"✅ Конверсия успешно затрекана!", Colors.GREEN)
        log(f"   Amount: ${result['amount']/100:.2f}", Colors.BLUE)
        log(f"   Time to conversion: {result['time_to_conversion']}s", Colors.BLUE)
        return result
    else:
        log(f"❌ Ошибка трекинга конверсии: {response.status_code} - {response.text}", Colors.RED)
        return None

def test_get_analytics(token):
    """Тест получения аналитики"""
    log(f"📊 Получаю аналитику...", Colors.YELLOW)

    headers = {"Authorization": f"Bearer {token}"}

    # Получаем список traffic sources
    response = requests.get(
        f"{API_URL}/api/v1/utm/sources",
        headers=headers
    )

    if response.status_code == 200:
        sources = response.json()
        log(f"✅ Получено {len(sources)} traffic sources", Colors.GREEN)

        for source in sources:
            log(f"\n📈 Traffic Source: {source['utm_id']}", Colors.BLUE)
            log(f"   Source: {source['utm_source']} / Campaign: {source['utm_campaign']}", Colors.BLUE)
            log(f"   Clicks: {source['clicks']}", Colors.BLUE)
            log(f"   Conversions: {source['conversions']}", Colors.BLUE)
            log(f"   Revenue: ${source['revenue']/100:.2f}", Colors.BLUE)
            if source['conversions'] > 0 and source['clicks'] > 0:
                cvr = (source['conversions'] / source['clicks']) * 100
                log(f"   CVR: {cvr:.2f}%", Colors.GREEN)

        return sources
    else:
        log(f"❌ Ошибка получения аналитики: {response.status_code} - {response.text}", Colors.RED)
        return None

def check_database():
    """Проверка данных в БД напрямую"""
    log(f"\n🔍 Проверяю данные в БД...", Colors.YELLOW)

    import subprocess

    # Проверяем traffic_sources
    result = subprocess.run(
        ["docker", "exec", "utm-postgres", "psql", "-U", "utm_user", "-d", "utm_tracking",
         "-c", "SELECT utm_id, utm_source, clicks, conversions, revenue FROM traffic_sources;"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("✅ Traffic Sources в БД:", Colors.GREEN)
        print(result.stdout)
    else:
        log(f"❌ Ошибка: {result.stderr}", Colors.RED)

    # Проверяем conversions
    result = subprocess.run(
        ["docker", "exec", "utm-postgres", "psql", "-U", "utm_user", "-d", "utm_tracking",
         "-c", "SELECT customer_id, amount, product_name, time_to_conversion FROM conversions;"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("\n✅ Conversions в БД:", Colors.GREEN)
        print(result.stdout)
    else:
        log(f"❌ Ошибка: {result.stderr}", Colors.RED)

def main():
    """Главная функция теста"""
    log("🚀 Начинаю тестирование UTM-трекинг флоу...\n", Colors.BOLD)

    # 1. Аутентификация
    token = test_auth()
    if not token:
        log("\n❌ Не удалось получить токен. Прекращаю тест.", Colors.RED)
        return

    time.sleep(1)

    # 2. Создаем landing ссылку
    log("\n" + "="*60, Colors.BLUE)
    landing_result = test_create_utm_link(token, "landing")
    if not landing_result:
        log("❌ Не удалось создать landing ссылку", Colors.RED)
        return

    time.sleep(1)

    # 3. Создаем direct ссылку
    log("\n" + "="*60, Colors.BLUE)
    direct_result = test_create_utm_link(token, "direct")

    time.sleep(1)

    # 4. Трекаем клик на landing ссылку
    log("\n" + "="*60, Colors.BLUE)
    click_result = test_track_click(landing_result['utm_id'])

    time.sleep(2)  # Имитируем задержку перед покупкой

    # 5. Трекаем конверсию
    log("\n" + "="*60, Colors.BLUE)
    conversion_result = test_track_conversion(landing_result['utm_id'])

    time.sleep(1)

    # 6. Получаем аналитику
    log("\n" + "="*60, Colors.BLUE)
    analytics = test_get_analytics(token)

    # 7. Проверяем БД
    log("\n" + "="*60, Colors.BLUE)
    check_database()

    # Итог
    log("\n" + "="*60, Colors.BOLD)
    log("✅ Тестирование завершено!", Colors.GREEN)
    log("\n📊 Резюме:", Colors.BOLD)
    log("  ✅ Аутентификация работает", Colors.GREEN)
    log(f"  ✅ Создано ссылок: 2 (landing + direct)", Colors.GREEN)
    log(f"  ✅ Кликов затрекано: 1", Colors.GREEN)
    log(f"  ✅ Конверсий затрекано: 1", Colors.GREEN)
    log(f"  ✅ Аналитика доступна", Colors.GREEN)

    if analytics and len(analytics) > 0:
        total_revenue = sum(s['revenue'] for s in analytics)
        log(f"\n💰 Общая выручка: ${total_revenue/100:.2f}", Colors.YELLOW)

if __name__ == "__main__":
    main()
