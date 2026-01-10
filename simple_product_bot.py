#!/usr/bin/env python3
"""
Простой Telegram бот для тестирования UTM трекинга с продуктом.

Флоу:
1. User кликает UTM ссылку → Landing → Redirect в бот
2. /start creative_abc123 → сохраняем UTM ID
3. /buy → оплата → webhook конверсии
"""

import telebot
import requests
import json

# Настройки
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Получи у @BotFather
TRACKING_API = "http://localhost:8000"  # Твой API

bot = telebot.TeleBot(BOT_TOKEN)

# Простое хранилище: user_id → utm_id
# В проде используй Redis или БД
user_utm_map = {}


@bot.message_handler(commands=['start'])
def start(message):
    """
    Обрабатывает /start команду с UTM параметром.

    Формат: /start creative_abc123
    """
    user_id = message.from_user.id

    # Извлекаем UTM ID из параметра
    args = message.text.split()

    if len(args) > 1:
        utm_id = args[1]

        # Сохраняем связь user ↔ UTM
        user_utm_map[user_id] = utm_id

        print(f"✅ User {user_id} linked to UTM: {utm_id}")

        # Трекаем что юзер зашел в бота (опционально)
        try:
            requests.post(
                f"{TRACKING_API}/api/v1/utm/track/click",
                json={
                    "utm_id": utm_id,
                    "landing_page": "telegram_bot",
                    "referrer": "landing_page"
                },
                timeout=2
            )
        except:
            pass  # Не критично если не залогировалось

        bot.send_message(
            message.chat.id,
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            f"🎁 Добро пожаловать в наш продукт!\n\n"
            f"📦 Что мы предлагаем:\n"
            f"• Премиум доступ - $10/мес\n"
            f"• Безлимитные функции\n"
            f"• Приоритетная поддержка\n\n"
            f"💰 Команды:\n"
            f"/buy - Купить доступ\n"
            f"/info - Узнать больше"
        )
    else:
        # Зашел без UTM (прямая ссылка)
        bot.send_message(
            message.chat.id,
            "👋 Привет! Это тестовый бот.\n\n"
            "Для работы используй ссылку из нашей рекламы!"
        )


@bot.message_handler(commands=['buy'])
def buy(message):
    """
    Симуляция покупки и трекинг конверсии.
    """
    user_id = message.from_user.id

    # Проверяем есть ли UTM у этого юзера
    utm_id = user_utm_map.get(user_id)

    if not utm_id:
        bot.send_message(
            message.chat.id,
            "⚠️ Сначала используй ссылку из рекламы!\n"
            "Команда: /start <utm_code>"
        )
        return

    # В реальной жизни тут была бы оплата:
    # - Telegram Stars
    # - Stripe
    # - PayPal
    # - etc.

    # Пока просто симулируем успешную оплату
    bot.send_message(
        message.chat.id,
        "💳 Обрабатываем оплату...\n"
        "(это тест, реальная оплата не происходит)"
    )

    # ТРЕКАЕМ КОНВЕРСИЮ через webhook
    try:
        response = requests.post(
            f"{TRACKING_API}/api/v1/utm/webhook/conversion",
            json={
                "utm_id": utm_id,
                "customer_id": f"telegram_{user_id}",
                "amount": 1000,  # $10.00 в центах
                "currency": "USD",
                "product_name": "Premium Access",
                "conversion_type": "purchase",
                "metadata": {
                    "user_name": message.from_user.username or "unknown",
                    "test_mode": True
                }
            },
            timeout=5
        )

        if response.status_code == 200:
            print(f"✅ Conversion tracked for UTM: {utm_id}")

            bot.send_message(
                message.chat.id,
                "✅ Покупка успешна! (тест)\n\n"
                f"🎉 Спасибо за покупку!\n"
                f"💰 Сумма: $10.00\n\n"
                f"📊 Конверсия затрекана в аналитику!\n"
                f"UTM: {utm_id}"
            )
        else:
            raise Exception(f"API returned {response.status_code}")

    except Exception as e:
        print(f"❌ Error tracking conversion: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Покупка прошла, но не удалось затрекать.\n"
            f"Ошибка: {str(e)}"
        )


@bot.message_handler(commands=['info'])
def info(message):
    """Информация о продукте."""
    user_id = message.from_user.id
    utm_id = user_utm_map.get(user_id, "Не задан")

    bot.send_message(
        message.chat.id,
        f"ℹ️ Информация:\n\n"
        f"👤 User ID: {user_id}\n"
        f"🔗 UTM ID: {utm_id}\n\n"
        f"📦 Продукт:\n"
        f"• Premium Access\n"
        f"• Цена: $10/месяц\n\n"
        f"Команды:\n"
        f"/buy - Купить\n"
        f"/start - Начать заново"
    )


@bot.message_handler(commands=['stats'])
def stats(message):
    """Показывает сколько юзеров с UTM."""
    total_users = len(user_utm_map)

    bot.send_message(
        message.chat.id,
        f"📊 Статистика:\n\n"
        f"👥 Всего пользователей с UTM: {total_users}\n\n"
        f"Это тестовый бот для проверки UTM трекинга."
    )


if __name__ == "__main__":
    print("🤖 Бот запущен!")
    print(f"📊 Tracking API: {TRACKING_API}")
    print("⏳ Ожидаю сообщений...")

    # Запуск бота
    bot.infinity_polling()
