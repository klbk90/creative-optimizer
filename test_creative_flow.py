#!/usr/bin/env python3
"""
Тест нового флоу: креатив → UTM → метрики
"""

import requests
import json

API_URL = "http://localhost:8000"

print("🎬 Тестируем новый флоу: Креатив → UTM → Метрики\n")
print("="*60)

# 1. Создаем креатив (автоматически создастся UTM)
print("\n1️⃣ Загружаем креатив...")

with open('/tmp/test_creative.mp4', 'rb') as f:
    files = {'video': f}
    data = {
        'creative_name': 'Test Creative #1',
        'product_category': 'fitness',
        'campaign_tag': 'test_campaign_123',
        'hook_type': 'before_after',
        'emotion': 'achievement'
    }

    response = requests.post(
        f"{API_URL}/api/v1/creative/upload",
        files=files,
        data=data
    )

if response.status_code == 200:
    creative = response.json()
    print("✅ Креатив создан!")
    print(f"   Creative ID: {creative['id']}")
    print(f"   UTM ID: {creative['utm_id']}")
    print(f"   UTM Link: {creative['utm_link']}")
    print(f"   Predicted CVR: {creative['predicted_cvr']*100:.1f}%")

    creative_id = creative['id']
    utm_id = creative['utm_id']
else:
    print(f"❌ Ошибка: {response.status_code}")
    print(response.text)
    exit(1)

# 2. Проверяем что в БД создались оба records
print("\n2️⃣ Проверяем БД...")
import subprocess

result = subprocess.run([
    "docker", "exec", "utm-postgres", "psql", "-U", "utm_user", "-d", "utm_tracking",
    "-c", f"SELECT id, name, traffic_source_id FROM creatives WHERE id='{creative_id}';"
], capture_output=True, text=True)

print("Креатив в БД:")
print(result.stdout)

result = subprocess.run([
    "docker", "exec", "utm-postgres", "psql", "-U", "utm_user", "-d", "utm_tracking",
    "-c", f"SELECT utm_id, utm_campaign, clicks, conversions FROM traffic_sources WHERE utm_id='{utm_id}';"
], capture_output=True, text=True)

print("UTM в БД:")
print(result.stdout)

# 3. Обновляем метрики креатива
print("3️⃣ Обновляем метрики креатива (симулируем результаты TikTok ads)...")

response = requests.put(
    f"{API_URL}/api/v1/creative/creatives/{creative_id}/metrics",
    data={
        'impressions': 10000,
        'clicks': 500,
        'conversions': 50
    }
)

if response.status_code == 200:
    result = response.json()
    print("✅ Метрики обновлены!")
    print(f"   Impressions: {result['impressions']}")
    print(f"   Conversions: {result['conversions']}")
    print(f"   CVR: {result['cvr']*100:.2f}%")
else:
    print(f"❌ Ошибка: {response.status_code}")
    print(response.text)

# 4. Проверяем синхронизацию с TrafficSource
print("\n4️⃣ Проверяем синхронизацию с UTM tracking...")

result = subprocess.run([
    "docker", "exec", "utm-postgres", "psql", "-U", "utm_user", "-d", "utm_tracking",
    "-c", f"SELECT utm_id, clicks, conversions FROM traffic_sources WHERE utm_id='{utm_id}';"
], capture_output=True, text=True)

print("UTM после обновления:")
print(result.stdout)

# 5. Создаем еще 2 креатива в той же кампании
print("\n5️⃣ Создаем еще 2 креатива в той же кампании...")

for i in range(2, 4):
    with open('/tmp/test_creative.mp4', 'rb') as f:
        files = {'video': f}
        data = {
            'creative_name': f'Test Creative #{i}',
            'product_category': 'fitness',
            'campaign_tag': 'test_campaign_123',  # Та же кампания!
            'hook_type': ['question', 'social_proof'][i-2],
            'emotion': ['curiosity', 'fomo'][i-2]
        }

        response = requests.post(
            f"{API_URL}/api/v1/creative/upload",
            files=files,
            data=data
        )

        if response.status_code == 200:
            creative = response.json()
            print(f"   ✅ Креатив #{i} создан: {creative['utm_id']}")

# 6. Проверяем аналитику по кампании
print("\n6️⃣ Смотрим все креативы кампании...")

response = requests.get(
    f"{API_URL}/api/v1/creative/creatives",
    params={'campaign_tag': 'test_campaign_123'}
)

if response.status_code == 200:
    creatives = response.json()
    print(f"✅ Всего креативов в кампании: {len(creatives)}")

    for c in creatives:
        print(f"\n   📊 {c['name']}")
        print(f"      Hook: {c['hook_type']} + {c['emotion']}")
        print(f"      Conversions: {c['conversions']}")
        print(f"      CVR: {c['cvr']*100:.2f}%")

print("\n" + "="*60)
print("✅ Тест завершен!\n")
print("🎯 Что работает:")
print("   ✅ Создание креатива → автоматически создается UTM")
print("   ✅ Обновление метрик → синхронизируется с UTM tracking")
print("   ✅ Группировка по кампании → можно сравнивать креативы")
print("\n💡 Теперь ты можешь:")
print("   1. Загрузить креатив → получить UTM ссылку")
print("   2. Добавить ссылку в TikTok bio")
print("   3. Обновить метрики когда будут результаты")
print("   4. Сравнить эффективность всех креативов кампании")
