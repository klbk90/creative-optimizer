#!/usr/bin/env python3
"""
Environment Configuration Checker
Проверяет, что все необходимые переменные окружения настроены правильно
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружен файл: {env_path}")
else:
    print(f"❌ Файл .env не найден: {env_path}")
    print("   Скопируйте .env.example в .env и заполните необходимые значения")
    sys.exit(1)

# Определяем обязательные и опциональные переменные
REQUIRED_FOR_API = {
    'DATABASE_URL': 'PostgreSQL connection string',
    'REDIS_URL': 'Redis connection string',
    'JWT_SECRET_KEY': 'JWT secret for authentication',
}

REQUIRED_FOR_BOT = {
    'ADMIN_BOT_TOKEN': 'Telegram Admin Bot token from @BotFather',
    'TRACKING_API_URL': 'URL of tracking API',
    'ADMIN_IDS': 'Comma-separated admin Telegram IDs',
}

OPTIONAL = {
    'TG_API_ID': 'Telegram API ID (for advanced features)',
    'TG_API_HASH': 'Telegram API Hash (for advanced features)',
    'ANTHROPIC_API_KEY': 'Anthropic API key (for AI features)',
    'REPLICATE_API_TOKEN': 'Replicate token (for image generation)',
    'GOOGLE_API_KEY': 'Google API key (for image search)',
    'TELEGRAM_BOT_USERNAME': 'Bot username for landing page redirects',
}

def check_variable(var_name: str, description: str, required: bool = True) -> bool:
    """Проверяет одну переменную окружения"""
    value = os.getenv(var_name)

    if not value or value.strip() == '':
        if required:
            print(f"❌ {var_name:30} - НЕ ЗАПОЛНЕНО (обязательно)")
            print(f"   {description}")
            return False
        else:
            print(f"⚠️  {var_name:30} - не заполнено (опционально)")
            return True
    else:
        # Скрываем секретные значения
        if 'KEY' in var_name or 'TOKEN' in var_name or 'SECRET' in var_name or 'HASH' in var_name:
            display_value = value[:10] + '...' if len(value) > 10 else '***'
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value

        print(f"✅ {var_name:30} - {display_value}")
        return True

def main():
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("="*80 + "\n")

    all_ok = True

    # Проверяем обязательные для API
    print("📌 ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ API:")
    print("-" * 80)
    for var_name, description in REQUIRED_FOR_API.items():
        if not check_variable(var_name, description, required=True):
            all_ok = False

    # Проверяем обязательные для бота
    print("\n📌 ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ADMIN BOT:")
    print("-" * 80)
    for var_name, description in REQUIRED_FOR_BOT.items():
        if not check_variable(var_name, description, required=True):
            all_ok = False

    # Проверяем опциональные
    print("\n📌 ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ:")
    print("-" * 80)
    for var_name, description in OPTIONAL.items():
        check_variable(var_name, description, required=False)

    # Итоговый результат
    print("\n" + "="*80)
    if all_ok:
        print("✅ ВСЕ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ НАСТРОЕНЫ!")
        print("\n📝 Следующие шаги:")
        print("   1. Запустите docker-compose up -d (PostgreSQL + Redis)")
        print("   2. Запустите миграции: alembic upgrade head")
        print("   3. Запустите API: uvicorn api.main:app --reload")
        print("   4. Запустите admin bot: python bots/admin_bot.py")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ НЕКОТОРЫЕ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ НЕ НАСТРОЕНЫ")
        print("\n📝 Что делать:")
        print("   1. Откройте файл .env")
        print("   2. Заполните отмеченные ❌ переменные")
        print("   3. Запустите этот скрипт снова: python check_env.py")
        print("="*80 + "\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
