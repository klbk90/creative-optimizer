"""
Integration example for tg-reposter with UTM tracking.

This shows how to add UTM tracking links to your reposted messages.
"""

import os
import requests
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

TRACKING_API_URL = os.getenv("TRACKING_API_URL", "http://localhost:8000")
TRACKING_API_TOKEN = os.getenv("TRACKING_API_TOKEN")  # JWT token from /api/v1/auth/login


# ============================================================================
# UTM Link Generator
# ============================================================================

def generate_utm_link_for_repost(
    campaign: str,
    content: Optional[str] = None,
    bot_username: str = "your_bot"
) -> Optional[str]:
    """
    Generate direct TG link for reposts.

    Args:
        campaign: Campaign name (e.g., "repost_jan_2025")
        content: Content identifier (e.g., post ID or channel name)
        bot_username: Your bot username (without @)

    Returns:
        UTM tracking link or None
    """
    try:
        response = requests.post(
            f"{TRACKING_API_URL}/api/v1/utm/generate",
            headers={
                "Authorization": f"Bearer {TRACKING_API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "base_url": f"https://t.me/{bot_username}",
                "source": "telegram",
                "medium": "repost",
                "campaign": campaign,
                "content": content,
                "link_type": "direct"  # Important: use direct link for Telegram
            },
            timeout=5
        )

        if response.status_code in [200, 201]:
            data = response.json()
            return data["utm_link"]
        else:
            print(f"❌ Failed to generate UTM link: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error generating UTM link: {e}")
        return None


# ============================================================================
# Repost Enhancement
# ============================================================================

def add_utm_to_repost(
    original_text: str,
    source_channel: str,
    campaign: str = "repost_2025",
    bot_username: str = "your_bot",
    add_cta: bool = True
) -> str:
    """
    Add UTM tracking link to reposted message.

    Args:
        original_text: Original message text
        source_channel: Source channel name
        campaign: UTM campaign name
        bot_username: Your bot username
        add_cta: Whether to add call-to-action

    Returns:
        Enhanced text with UTM link
    """
    # Generate UTM link
    utm_link = generate_utm_link_for_repost(
        campaign=campaign,
        content=source_channel,
        bot_username=bot_username
    )

    if not utm_link:
        # Fallback: return original with simple link
        utm_link = f"https://t.me/{bot_username}"

    # Build enhanced message
    enhanced_text = original_text

    if add_cta:
        # Add call-to-action with UTM link
        cta = f"\n\n💰 Хочешь зарабатывать? → {utm_link}"
        enhanced_text += cta
    else:
        # Just append the link
        enhanced_text += f"\n\n{utm_link}"

    return enhanced_text


# ============================================================================
# Example Integration with tg-reposter
# ============================================================================

def example_telethon_integration():
    """
    Example integration with Telethon-based reposter.
    """
    from telethon import TelegramClient, events

    api_id = int(os.getenv("TG_API_ID"))
    api_hash = os.getenv("TG_API_HASH")
    client = TelegramClient('reposter', api_id, api_hash)

    SOURCE_CHANNELS = ["@sports_channel", "@football_news"]
    TARGET_CHANNEL = "@your_target_channel"
    BOT_USERNAME = "your_lootbox_bot"

    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def handle_new_message(event):
        """Handle new message from source channels."""
        original_text = event.message.text or ""

        # Skip if empty or already processed
        if not original_text or "Хочешь зарабатывать?" in original_text:
            return

        # Get source channel name
        source_channel = event.chat.username or event.chat.title

        # Add UTM tracking link
        enhanced_text = add_utm_to_repost(
            original_text=original_text,
            source_channel=source_channel,
            campaign="repost_jan_2025",
            bot_username=BOT_USERNAME,
            add_cta=True
        )

        # Send to target channel
        if event.message.media:
            await client.send_file(
                TARGET_CHANNEL,
                event.message.media,
                caption=enhanced_text
            )
        else:
            await client.send_message(
                TARGET_CHANNEL,
                enhanced_text
            )

        print(f"✅ Reposted from {source_channel} with UTM tracking")

    print("🤖 Reposter with UTM tracking started...")
    client.start()
    client.run_until_disconnected()


def example_pyrogram_integration():
    """
    Example integration with Pyrogram-based reposter.
    """
    from pyrogram import Client, filters

    app = Client(
        "reposter",
        api_id=os.getenv("TG_API_ID"),
        api_hash=os.getenv("TG_API_HASH")
    )

    SOURCE_CHANNELS = ["@sports_channel", "@football_news"]
    TARGET_CHANNEL = "@your_target_channel"
    BOT_USERNAME = "your_lootbox_bot"

    @app.on_message(filters.chat(SOURCE_CHANNELS))
    async def handle_message(client, message):
        """Handle new message from source channels."""
        original_text = message.text or message.caption or ""

        if not original_text:
            return

        # Get source channel
        source_channel = message.chat.username or message.chat.title

        # Add UTM link
        enhanced_text = add_utm_to_repost(
            original_text=original_text,
            source_channel=source_channel,
            campaign="repost_jan_2025",
            bot_username=BOT_USERNAME,
            add_cta=True
        )

        # Repost with UTM
        if message.media:
            await client.copy_message(
                TARGET_CHANNEL,
                message.chat.id,
                message.id,
                caption=enhanced_text
            )
        else:
            await client.send_message(
                TARGET_CHANNEL,
                enhanced_text
            )

        print(f"✅ Reposted from {source_channel} with UTM")

    print("🤖 Pyrogram reposter with UTM tracking started...")
    app.run()


# ============================================================================
# Advanced: Dynamic CTA based on content
# ============================================================================

def generate_smart_cta(original_text: str, utm_link: str) -> str:
    """
    Generate context-aware CTA based on content.

    Args:
        original_text: Original message
        utm_link: UTM tracking link

    Returns:
        Smart CTA text
    """
    text_lower = original_text.lower()

    # Sports-related CTAs
    if any(word in text_lower for word in ["гол", "футбол", "матч", "victory", "goal", "football"]):
        return f"\n\n⚽️ Обсудить матч и получить бонус → {utm_link}"

    # Crypto-related
    if any(word in text_lower for word in ["bitcoin", "crypto", "btc", "eth", "крипто"]):
        return f"\n\n💰 Получи криптобонус → {utm_link}"

    # News-related
    if any(word in text_lower for word in ["новост", "news", "breaking", "exclusive"]):
        return f"\n\n📰 Больше новостей в боте → {utm_link}"

    # Default
    return f"\n\n🎁 Открыть лутбокс → {utm_link}"


def add_smart_utm_to_repost(
    original_text: str,
    source_channel: str,
    campaign: str,
    bot_username: str
) -> str:
    """
    Add smart context-aware UTM link to repost.

    Args:
        original_text: Original message
        source_channel: Source channel
        campaign: Campaign name
        bot_username: Bot username

    Returns:
        Enhanced text with smart CTA
    """
    # Generate UTM link
    utm_link = generate_utm_link_for_repost(
        campaign=campaign,
        content=source_channel,
        bot_username=bot_username
    )

    if not utm_link:
        utm_link = f"https://t.me/{bot_username}"

    # Generate smart CTA
    smart_cta = generate_smart_cta(original_text, utm_link)

    return original_text + smart_cta


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("""
🔗 TG-Reposter UTM Integration Example

This demonstrates how to add UTM tracking to reposted messages.

Setup:
1. Set TRACKING_API_URL and TRACKING_API_TOKEN in .env
2. Configure your bot username
3. Run reposter with UTM tracking

Example usage:
    """)

    # Test UTM link generation
    test_link = generate_utm_link_for_repost(
        campaign="test_campaign",
        content="test_channel",
        bot_username="your_bot"
    )

    if test_link:
        print(f"✅ Generated test link: {test_link}")
    else:
        print("❌ Failed to generate test link. Check API connection.")

    # Test message enhancement
    test_text = "⚽️ Гол Месси в ворота Реала!"
    enhanced = add_smart_utm_to_repost(
        original_text=test_text,
        source_channel="@football_news",
        campaign="test",
        bot_username="your_bot"
    )

    print(f"\nOriginal: {test_text}")
    print(f"Enhanced: {enhanced}")

    print("\n💡 To run reposter, uncomment one of the examples above.")
