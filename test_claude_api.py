#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Claude API.
Проверяет:
1. Работает ли API ключ
2. Какие модели доступны
3. Работает ли Vision API
"""

import os
import sys

# Проверяем есть ли API ключ
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY not set!")
    print("Set it: export ANTHROPIC_API_KEY='sk-ant-api03-...'")
    sys.exit(1)

print(f"🔑 API Key found: sk-ant-api03-***{ANTHROPIC_API_KEY[-4:]}")
print()

# Импортируем библиотеку
try:
    import anthropic
    print(f"✅ anthropic SDK version: {anthropic.__version__}")
except ImportError:
    print("❌ anthropic not installed!")
    print("Install: pip install anthropic")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 1: Simple text message (no vision)")
print("=" * 60)

# Тест 1: Простой текстовый запрос
models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

working_model = None
for model in models_to_test:
    try:
        print(f"\nTesting model: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Hi' in one word"}]
        )
        print(f"  ✅ SUCCESS! Response: {response.content[0].text}")
        working_model = model
        break
    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "not_found" in error_str:
            print(f"  ❌ 404 - Model not found")
        elif "401" in error_str or "authentication" in error_str:
            print(f"  ❌ 401 - Invalid API key")
        else:
            print(f"  ❌ Error: {error_str[:100]}")

if not working_model:
    print("\n❌ NO WORKING MODEL FOUND!")
    print("\nPossible issues:")
    print("1. API key is invalid or expired")
    print("2. Account doesn't have access to these models")
    print("3. Need to upgrade anthropic SDK: pip install --upgrade anthropic")
    sys.exit(1)

print()
print("=" * 60)
print(f"TEST 2: Vision API with {working_model}")
print("=" * 60)

# Тест 2: Vision API с изображением
try:
    import base64

    # Создаем простое тестовое изображение (1x1 красный пиксель PNG)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

    print(f"\nTesting Vision API with {working_model}")
    response = client.messages.create(
        model=working_model,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is this image?"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": test_image_base64
                    }
                }
            ]
        }]
    )
    print(f"  ✅ Vision API works! Response: {response.content[0].text}")

except Exception as e:
    error_str = str(e)
    print(f"  ❌ Vision API failed: {error_str[:200]}")
    print("\nPossible issues:")
    print("1. Model doesn't support Vision API")
    print("2. Account doesn't have access to Vision features")
    print("3. Image format is incorrect")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"✅ Working model: {working_model}")
print(f"📝 Update your code to use: model=\"{working_model}\"")
print()
