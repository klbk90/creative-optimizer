"""
Telegram Admin Bot для управления UTM метками и аналитики.

Команды:
- /generate - создать новую UTM ссылку
- /stats - статистика
- /campaigns - список кампаний
- /top - топ источников
- /conversions - последние конверсии
- /settings - настройки уведомлений
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import schedule
import threading
import time

load_dotenv()

# ============================================================================
# Конфигурация
# ============================================================================

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
API_BASE_URL = os.getenv("TRACKING_API_URL", "http://localhost:8000")
ADMIN_JWT_TOKEN = os.getenv("ADMIN_JWT_TOKEN")  # JWT для API запросов

# Список админов (Telegram User IDs)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Базовый URL для landing pages
LANDING_BASE_URL = os.getenv("LANDING_BASE_URL", "http://localhost:8000/api/v1/landing/l")

bot = TeleBot(ADMIN_BOT_TOKEN)

# Хранилище состояний пользователей
user_states = {}


# ============================================================================
# Хелперы для API запросов
# ============================================================================

def api_request(method: str, endpoint: str, data: Optional[dict] = None) -> Optional[dict]:
    """
    Выполнить запрос к tracking API.

    Args:
        method: GET, POST, etc.
        endpoint: /api/v1/utm/generate
        data: JSON данные для POST

    Returns:
        Response JSON или None если ошибка
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if ADMIN_JWT_TOKEN:
        headers["Authorization"] = f"Bearer {ADMIN_JWT_TOKEN}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return None

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code} {response.text}")
            return None

    except Exception as e:
        print(f"❌ API Request failed: {e}")
        return None


def format_money(cents: int) -> str:
    """Форматировать деньги из центов в доллары."""
    return f"${cents / 100:.2f}"


def format_percentage(value: float) -> str:
    """Форматировать процент."""
    return f"{value:.1f}%"


def check_admin(user_id: int) -> bool:
    """Проверить что пользователь - админ."""
    return user_id in ADMIN_IDS


# ============================================================================
# Декоратор для проверки прав админа
# ============================================================================

def admin_only(func):
    """Декоратор: только для админов."""
    def wrapper(message):
        if not check_admin(message.from_user.id):
            bot.reply_to(message, "❌ У вас нет доступа к этому боту.")
            return
        return func(message)
    return wrapper


# ============================================================================
# Команды бота
# ============================================================================

@bot.message_handler(commands=['start', 'help'])
@admin_only
def handle_start(message):
    """Стартовое сообщение."""
    user_name = message.from_user.first_name

    text = f"""
👋 Привет, {user_name}!

🤖 *Admin Bot для UTM трекинга*

📋 *Доступные команды:*

🔗 /generate - Создать UTM ссылку
📊 /stats - Статистика
📁 /campaigns - Список кампаний
🏆 /top - Топ источников
💰 /conversions - Последние покупки
⚙️ /settings - Настройки

ℹ️ /help - Показать это сообщение
"""

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['generate'])
@admin_only
def handle_generate(message):
    """
    Начать процесс генерации UTM ссылки.
    """
    user_id = message.from_user.id

    # Сохраняем состояние
    user_states[user_id] = {"action": "generate_utm", "step": "campaign"}

    msg = bot.send_message(
        message.chat.id,
        "🔗 *Генератор UTM ссылок*\n\n"
        "Введите название кампании:\n"
        "_(например: football_jan_2025)_",
        parse_mode="Markdown"
    )

    bot.register_next_step_handler(msg, process_campaign_name)


def process_campaign_name(message):
    """Обработать название кампании."""
    user_id = message.from_user.id
    campaign_name = message.text.strip()

    if not campaign_name:
        bot.reply_to(message, "❌ Название кампании не может быть пустым. Попробуйте /generate снова.")
        user_states.pop(user_id, None)
        return

    # Сохранить название кампании
    user_states[user_id]["campaign"] = campaign_name
    user_states[user_id]["step"] = "link_type"

    # Показать кнопки выбора типа ссылки
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🌐 С Landing Page (для TikTok bio)", callback_data="linktype_landing"),
        InlineKeyboardButton("📱 Прямая TG ссылка (для репостов)", callback_data="linktype_direct")
    )

    bot.send_message(
        message.chat.id,
        f"✅ Кампания: *{campaign_name}*\n\n"
        f"Выберите тип ссылки:\n\n"
        f"🌐 *Landing* - промежуточная страница с редиректом\n"
        f"   _(для TikTok, Instagram bio)_\n\n"
        f"📱 *Direct* - прямая ссылка на бота/канал\n"
        f"   _(для tg-reposter, постов в канале)_",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("linktype_"))
def handle_link_type_selection(call):
    """Обработать выбор типа ссылки."""
    user_id = call.from_user.id
    link_type = call.data.replace("linktype_", "")

    if user_id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла. Начните с /generate")
        return

    user_states[user_id]["link_type"] = link_type
    user_states[user_id]["step"] = "source"

    bot.answer_callback_query(call.id)

    # Показать кнопки выбора источника
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📱 TikTok", callback_data="source_tiktok"),
        InlineKeyboardButton("📷 Instagram", callback_data="source_instagram"),
        InlineKeyboardButton("▶️ YouTube", callback_data="source_youtube"),
        InlineKeyboardButton("💬 Telegram", callback_data="source_telegram"),
        InlineKeyboardButton("🌐 Other", callback_data="source_other")
    )

    link_emoji = "🌐" if link_type == "landing" else "📱"
    link_name = "Landing Page" if link_type == "landing" else "Direct Link"

    bot.send_message(
        call.message.chat.id,
        f"✅ Тип ссылки: {link_emoji} *{link_name}*\n\n"
        f"Выберите источник трафика:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("source_"))
def handle_source_selection(call):
    """Обработать выбор источника."""
    user_id = call.from_user.id
    source = call.data.replace("source_", "")

    if user_id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла. Начните с /generate")
        return

    user_states[user_id]["source"] = source
    user_states[user_id]["step"] = "content"

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        f"✅ Источник: *{source}*\n\n"
        f"Введите content (ID видео или вариант креатива):\n"
        f"_(например: video_123 или можно пропустить - отправьте -)_",
        parse_mode="Markdown"
    )

    bot.register_next_step_handler(msg, process_content)


def process_content(message):
    """Обработать content."""
    user_id = message.from_user.id
    content = message.text.strip()

    if content == "-":
        content = None

    user_states[user_id]["content"] = content

    # Генерируем UTM ссылку
    campaign = user_states[user_id]["campaign"]
    source = user_states[user_id]["source"]
    link_type = user_states[user_id].get("link_type", "landing")

    # Определяем base_url в зависимости от типа ссылки
    if link_type == "landing":
        base_url = LANDING_BASE_URL
    else:
        # Для direct ссылок используем канал/бота из ENV или дефолт
        base_url = os.getenv("DEFAULT_TELEGRAM_CHANNEL", "https://t.me/sportschannel")

    # API запрос
    result = api_request("POST", "/api/v1/utm/generate", {
        "base_url": base_url,
        "source": source,
        "campaign": campaign,
        "content": content,
        "medium": "social",
        "link_type": link_type
    })

    if not result or not result.get("success"):
        bot.send_message(
            message.chat.id,
            "❌ Ошибка при создании UTM ссылки. Проверьте настройки API."
        )
        user_states.pop(user_id, None)
        return

    utm_link = result["utm_link"]
    utm_id = result["utm_id"]
    link_type = result.get("link_type", "landing")

    # Красивый ответ
    link_emoji = "🌐" if link_type == "landing" else "📱"
    link_description = "Landing Page" if link_type == "landing" else "Direct Link"

    usage_hint = ""
    if link_type == "landing":
        usage_hint = f"📋 Скопируйте ссылку и вставьте в bio {source}!"
    else:
        usage_hint = "📋 Используйте эту ссылку в постах или репостах!"

    text = f"""
✅ *UTM ссылка создана!*

{link_emoji} *Тип:* {link_description}
🔗 *Ссылка для {source}:*
`{utm_link}`

📊 *Параметры:*
• Campaign: `{campaign}`
• Source: `{source}`
• Content: `{content or 'не указан'}`
• UTM ID: `{utm_id}`
• Type: `{link_type}`

{usage_hint}
"""

    # Кнопки
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📊 Статистика", callback_data=f"campaign_stats_{campaign}"),
        InlineKeyboardButton("🔄 Создать еще", callback_data="generate_new")
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

    # Очистить состояние
    user_states.pop(user_id, None)


@bot.callback_query_handler(func=lambda call: call.data == "generate_new")
def handle_generate_new(call):
    """Создать новую UTM ссылку."""
    bot.answer_callback_query(call.id)
    handle_generate(call.message)


@bot.message_handler(commands=['stats'])
@admin_only
def handle_stats(message):
    """Показать статистику."""
    # Кнопки выбора периода
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("Сегодня", callback_data="stats_today"),
        InlineKeyboardButton("7 дней", callback_data="stats_week"),
        InlineKeyboardButton("30 дней", callback_data="stats_month")
    )

    bot.send_message(
        message.chat.id,
        "📊 *Статистика*\n\nВыберите период:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stats_"))
def handle_stats_period(call):
    """Показать статистику за период."""
    period = call.data.replace("stats_", "")

    # Определить даты
    date_to = datetime.now()
    if period == "today":
        date_from = datetime.now().replace(hour=0, minute=0, second=0)
        period_name = "сегодня"
    elif period == "week":
        date_from = date_to - timedelta(days=7)
        period_name = "за 7 дней"
    elif period == "month":
        date_from = date_to - timedelta(days=30)
        period_name = "за 30 дней"
    else:
        bot.answer_callback_query(call.id, "❌ Неверный период")
        return

    bot.answer_callback_query(call.id, "Загружаю статистику...")

    # Запрос к API
    result = api_request(
        "GET",
        f"/api/v1/analytics/dashboard?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
    )

    if not result or not result.get("success"):
        bot.send_message(call.message.chat.id, "❌ Ошибка при загрузке статистики")
        return

    summary = result["summary"]
    top_sources = result.get("top_sources", [])

    # Форматируем статистику
    text = f"""
📊 *Статистика {period_name}*

👆 *Клики:* {summary['total_clicks']}
💰 *Конверсии:* {summary['total_conversions']} (CR: {format_percentage(summary['conversion_rate'])})
💵 *Выручка:* {format_money(int(summary['total_revenue'] * 100))}
📈 *AOV:* {format_money(int(summary['avg_order_value'] * 100))}

🏆 *Топ источники:*
"""

    for i, source in enumerate(top_sources[:5], 1):
        text += f"{i}. {source['source'].upper()} - {source['conversions']} конв, {format_money(int(source['revenue'] * 100))}\n"

    if not top_sources:
        text += "_Нет данных_\n"

    # Кнопки
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 Обновить", callback_data=f"stats_{period}"),
        InlineKeyboardButton("📈 Детали", callback_data="stats_details")
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(commands=['campaigns'])
@admin_only
def handle_campaigns(message):
    """Показать список кампаний."""
    result = api_request("GET", "/api/v1/analytics/dashboard")

    if not result or not result.get("success"):
        bot.reply_to(message, "❌ Ошибка при загрузке кампаний")
        return

    campaigns = result.get("top_campaigns", [])

    if not campaigns:
        bot.send_message(message.chat.id, "📁 Кампании пока не созданы.\n\nИспользуйте /generate для создания первой кампании.")
        return

    text = "📁 *Активные кампании:*\n\n"

    for i, campaign in enumerate(campaigns, 1):
        name = campaign["campaign"]
        clicks = campaign["clicks"]
        conversions = campaign["conversions"]
        revenue = format_money(int(campaign["revenue"] * 100))
        cr = format_percentage(campaign["conversion_rate"])

        text += f"{i}. *{name}*\n"
        text += f"   👆 {clicks} | 💰 {conversions} ({cr}) | 💵 {revenue}\n\n"

    # Кнопки для каждой кампании
    markup = InlineKeyboardMarkup(row_width=1)
    for campaign in campaigns[:10]:
        name = campaign["campaign"]
        markup.add(
            InlineKeyboardButton(
                f"📊 {name}",
                callback_data=f"campaign_stats_{name}"
            )
        )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("campaign_stats_"))
def handle_campaign_stats(call):
    """Показать статистику кампании."""
    campaign_name = call.data.replace("campaign_stats_", "")

    bot.answer_callback_query(call.id, f"Загружаю {campaign_name}...")

    result = api_request("GET", f"/api/v1/analytics/campaign/{campaign_name}")

    if not result or not result.get("success"):
        bot.send_message(call.message.chat.id, f"❌ Ошибка при загрузке кампании {campaign_name}")
        return

    summary = result["summary"]
    performance = result["performance"]

    text = f"""
📊 *Кампания: {campaign_name}*

📹 *Видео:* {summary['total_videos']} ({summary['published_videos']} опубликовано)
👁 *Просмотры:* {summary['total_views']:,}
❤️ *Вовлеченность:* {summary['total_engagement']:,}

👆 *Клики:* {summary['total_clicks']}
💰 *Конверсии:* {summary['total_conversions']} (CR: {format_percentage(summary['conversion_rate'])})
💵 *Выручка:* {format_money(int(summary['total_revenue'] * 100))}

📈 *Показатели:*
• Выручка/видео: {format_money(int(performance['revenue_per_video'] * 100))}
• Выручка/клик: {format_money(int(performance['revenue_per_click'] * 100))}
• CTR (просмотры→клики): {format_percentage(performance['views_to_click_rate'])}
"""

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_campaigns"),
        InlineKeyboardButton("🔄 Обновить", callback_data=f"campaign_stats_{campaign_name}")
    )

    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(commands=['top'])
@admin_only
def handle_top(message):
    """Показать топ источников."""
    result = api_request("GET", "/api/v1/analytics/dashboard")

    if not result or not result.get("success"):
        bot.reply_to(message, "❌ Ошибка при загрузке данных")
        return

    top_sources = result.get("top_sources", [])

    if not top_sources:
        bot.send_message(message.chat.id, "🏆 Нет данных по источникам")
        return

    text = "🏆 *Топ источников по выручке:*\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, source in enumerate(top_sources[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = source["source"].upper()
        clicks = source["clicks"]
        conversions = source["conversions"]
        revenue = format_money(int(source["revenue"] * 100))
        cr = format_percentage(source["conversion_rate"])

        text += f"{medal} *{name}*\n"
        text += f"   👆 {clicks} кликов | 💰 {conversions} конв ({cr}) | 💵 {revenue}\n\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['conversions'])
@admin_only
def handle_conversions(message):
    """Показать последние конверсии."""
    result = api_request("GET", "/api/v1/utm/conversions?limit=20")

    if not result:
        bot.reply_to(message, "❌ Ошибка при загрузке конверсий")
        return

    conversions = result if isinstance(result, list) else []

    if not conversions:
        bot.send_message(message.chat.id, "💰 Конверсий пока нет")
        return

    text = "💰 *Последние 10 конверсий:*\n\n"

    for conv in conversions[:10]:
        amount = format_money(conv["amount"])
        product = conv.get("product_name", "Unknown")
        customer = conv.get("customer_id", "Unknown")
        created = datetime.fromisoformat(conv["created_at"].replace("Z", "+00:00"))
        time_ago = get_time_ago(created)

        text += f"• {amount} - {product}\n"
        text += f"  👤 User: {customer} | ⏰ {time_ago}\n\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['settings'])
@admin_only
def handle_settings(message):
    """Настройки уведомлений."""
    text = """
⚙️ *Настройки уведомлений*

🔔 Включить уведомления о:
"""

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✅ Новые конверсии", callback_data="toggle_notif_conversions"),
        InlineKeyboardButton("✅ Ежедневная статистика", callback_data="toggle_notif_daily"),
        InlineKeyboardButton("❌ Алерты (падение CR)", callback_data="toggle_notif_alerts")
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )


# ============================================================================
# Утилиты
# ============================================================================

def get_time_ago(dt: datetime) -> str:
    """Получить время 'X минут назад'."""
    now = datetime.now(dt.tzinfo)
    delta = now - dt

    if delta.days > 0:
        return f"{delta.days}д назад"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600}ч назад"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60}м назад"
    else:
        return "только что"


# ============================================================================
# Фоновые задачи
# ============================================================================

def send_daily_stats():
    """Отправить ежедневную статистику всем админам."""
    result = api_request("GET", "/api/v1/analytics/dashboard?date_from=" +
                        (datetime.now() - timedelta(days=1)).isoformat())

    if not result or not result.get("success"):
        return

    summary = result["summary"]

    text = f"""
📊 *Статистика за вчера*

👆 Клики: {summary['total_clicks']}
💰 Конверсии: {summary['total_conversions']} (CR: {format_percentage(summary['conversion_rate'])})
💵 Выручка: {format_money(int(summary['total_revenue'] * 100))}
📈 AOV: {format_money(int(summary['avg_order_value'] * 100))}
"""

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode="Markdown")
        except:
            pass


def schedule_tasks():
    """Запланировать фоновые задачи."""
    # Ежедневная статистика в 9:00
    schedule.every().day.at("09:00").do(send_daily_stats)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ============================================================================
# Запуск бота
# ============================================================================

if __name__ == "__main__":
    print("🤖 Admin Bot starting...")
    print(f"👤 Admins: {ADMIN_IDS}")
    print(f"📊 API: {API_BASE_URL}")

    if not ADMIN_IDS:
        print("⚠️  WARNING: No admin IDs configured! Set ADMIN_IDS in .env")

    # Запустить фоновые задачи в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_tasks, daemon=True)
    scheduler_thread.start()

    print("✅ Bot is running!")
    bot.infinity_polling()
