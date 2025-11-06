"""
Telegram User Bot Integration for UTM Tracking.

This module provides integration examples for tracking conversions
from your Telegram lootbox/game bot.

Integration Steps:
1. Track /start parameter (UTM ID)
2. Save UTM ID for user
3. Track conversion when user makes purchase
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime

# Configuration
TRACKING_API_URL = os.getenv("TRACKING_API_URL", "http://localhost:8000")
TRACKING_API_KEY = os.getenv("TRACKING_API_KEY", "")  # Optional for webhook endpoint


# ============================================================================
# In-Memory Storage (for demo - use database in production!)
# ============================================================================

# Store UTM IDs for users: {telegram_user_id: utm_id}
user_utm_mapping = {}


# ============================================================================
# Helper Functions
# ============================================================================

def track_click(utm_id: str, user_id: int, referrer: str = "telegram_direct") -> bool:
    """
    Track click for direct Telegram links.

    Call this when user clicks /start with utm_id parameter.

    Args:
        utm_id: UTM tracking ID
        user_id: Telegram user ID
        referrer: Source (default: telegram_direct)

    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{TRACKING_API_URL}/api/v1/utm/track/click",
            json={
                "utm_id": utm_id,
                "landing_page": None,  # Direct link, no landing page
                "referrer": referrer,
                "user_id": user_id,
            },
            timeout=5
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ Click tracking failed: {e}")
        return False


def track_conversion_webhook(
    utm_id: str,
    customer_id: str,
    amount: int,
    product_name: str = "Product",
    product_id: Optional[str] = None,
    conversion_type: str = "purchase",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Track conversion using webhook endpoint (no auth required).

    Call this when user makes a purchase.

    Args:
        utm_id: UTM tracking ID (from user_utm_mapping)
        customer_id: Customer identifier (e.g., telegram user ID)
        amount: Amount in cents (e.g., 5000 = $50.00)
        product_name: Product name
        product_id: Product identifier
        conversion_type: Type (purchase, signup, deposit)
        metadata: Additional data

    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{TRACKING_API_URL}/api/v1/utm/webhook/conversion",
            json={
                "utm_id": utm_id,
                "customer_id": customer_id,
                "conversion_type": conversion_type,
                "amount": amount,
                "currency": "USD",
                "product_id": product_id,
                "product_name": product_name,
                "metadata": metadata or {},
            },
            timeout=10
        )

        if response.status_code in [200, 201]:
            print(f"✅ Conversion tracked: ${amount/100:.2f} for {customer_id}")
            return True
        else:
            print(f"❌ Conversion tracking failed: {response.status_code} {response.text}")
            return False

    except Exception as e:
        print(f"❌ Conversion tracking error: {e}")
        return False


# ============================================================================
# Bot Integration Examples
# ============================================================================

def example_pytelegrambotapi():
    """
    Example integration with pyTelegramBotAPI (telebot).

    Install: pip install pyTelegramBotAPI
    """
    from telebot import TeleBot

    bot = TeleBot(os.getenv("BOT_TOKEN"))

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        """
        Handle /start command with UTM tracking.

        Example links:
        - t.me/your_bot?start=tiktok_abc123  (direct link)
        - t.me/your_bot?start=tg_xyz789     (from tg-reposter)
        """
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        # Extract UTM ID from /start parameter
        args = message.text.split(maxsplit=1)
        utm_id = args[1] if len(args) > 1 else None

        if utm_id and (utm_id.startswith("tiktok_") or utm_id.startswith("tg_") or utm_id.startswith("ig_")):
            # Save UTM for this user
            user_utm_mapping[user_id] = utm_id

            # Track click
            track_click(utm_id, user_id, referrer="telegram_bot_start")

            bot.send_message(
                message.chat.id,
                f"👋 Welcome {user_name}! Thanks for joining from our link!\n\n"
                f"🎁 Opening lootbox menu..."
            )
        else:
            bot.send_message(
                message.chat.id,
                f"👋 Welcome {user_name}!\n\n"
                f"🎁 Opening lootbox menu..."
            )

        # Show lootbox options
        # ... your bot logic here

    @bot.message_handler(commands=['buy'])
    def handle_buy(message):
        """Handle lootbox purchase."""
        user_id = message.from_user.id

        # ... your payment logic here ...

        # After successful payment:
        amount_cents = 5000  # $50.00
        product_name = "Gold Lootbox"

        # Track conversion if user came from UTM link
        if user_id in user_utm_mapping:
            utm_id = user_utm_mapping[user_id]
            track_conversion_webhook(
                utm_id=utm_id,
                customer_id=f"telegram_{user_id}",
                amount=amount_cents,
                product_name=product_name,
                product_id="lootbox_gold",
                metadata={
                    "payment_method": "telegram_stars",
                    "username": message.from_user.username,
                }
            )

        bot.send_message(
            message.chat.id,
            f"✅ Purchase successful! You got {product_name}!"
        )

    print("🤖 Bot starting...")
    bot.infinity_polling()


def example_python_telegram_bot():
    """
    Example integration with python-telegram-bot.

    Install: pip install python-telegram-bot
    """
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        # Extract UTM ID from /start parameter
        utm_id = context.args[0] if context.args else None

        if utm_id and (utm_id.startswith("tiktok_") or utm_id.startswith("tg_")):
            # Save UTM for this user
            user_utm_mapping[user_id] = utm_id

            # Track click
            track_click(utm_id, user_id, referrer="telegram_bot_start")

            await update.message.reply_text(
                f"👋 Welcome {user_name}! Thanks for joining from our link!\n\n"
                f"🎁 Opening lootbox menu..."
            )
        else:
            await update.message.reply_text(
                f"👋 Welcome {user_name}!\n\n🎁 Opening lootbox menu..."
            )

    async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle purchase."""
        user_id = update.effective_user.id

        # ... payment logic ...

        amount_cents = 5000
        product_name = "Gold Lootbox"

        # Track conversion
        if user_id in user_utm_mapping:
            utm_id = user_utm_mapping[user_id]
            track_conversion_webhook(
                utm_id=utm_id,
                customer_id=f"telegram_{user_id}",
                amount=amount_cents,
                product_name=product_name,
                product_id="lootbox_gold",
            )

        await update.message.reply_text(f"✅ Purchase successful!")

    # Build application
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))

    print("🤖 Bot starting...")
    app.run_polling()


# ============================================================================
# Stripe Integration Example
# ============================================================================

def track_stripe_conversion(
    session_id: str,
    customer_email: str,
    amount_cents: int,
    product_name: str
):
    """
    Track Stripe payment as conversion.

    Call this in Stripe webhook handler.

    Example Stripe webhook:
    ```python
    @app.post("/stripe/webhook")
    def stripe_webhook(request):
        event = stripe.Webhook.construct_event(...)

        if event.type == "checkout.session.completed":
            session = event.data.object

            # Extract user_id from metadata
            user_id = int(session.metadata.get("telegram_user_id"))

            # Track conversion
            if user_id in user_utm_mapping:
                track_stripe_conversion(
                    session.id,
                    session.customer_email,
                    session.amount_total,
                    "Gold Lootbox"
                )
    ```
    """
    # Find user by email or session metadata
    # In production: query database
    user_id = None  # Get from your database
    utm_id = user_utm_mapping.get(user_id)

    if utm_id:
        track_conversion_webhook(
            utm_id=utm_id,
            customer_id=customer_email,
            amount=amount_cents,
            product_name=product_name,
            metadata={
                "payment_method": "stripe",
                "session_id": session_id,
            }
        )


# ============================================================================
# Telegram Stars Integration Example
# ============================================================================

def example_telegram_stars_payment():
    """
    Example of Telegram Stars payment with UTM tracking.

    Telegram Stars: Native in-app payments in Telegram bots.
    """
    from telebot import TeleBot
    from telebot.types import LabeledPrice, PreCheckoutQuery

    bot = TeleBot(os.getenv("BOT_TOKEN"))

    @bot.message_handler(commands=['buy_stars'])
    def buy_with_stars(message):
        """Initiate Telegram Stars payment."""
        user_id = message.from_user.id

        prices = [LabeledPrice(label="Gold Lootbox", amount=5000)]  # 50 Stars

        bot.send_invoice(
            message.chat.id,
            title="Gold Lootbox",
            description="Premium lootbox with rare items!",
            invoice_payload=f"lootbox_gold_{user_id}",
            provider_token="",  # Empty for Stars
            currency="XTR",  # Telegram Stars
            prices=prices
        )

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query: PreCheckoutQuery):
        """Confirm payment before processing."""
        bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=True
        )

    @bot.message_handler(content_types=['successful_payment'])
    def successful_payment(message):
        """Handle successful Telegram Stars payment."""
        user_id = message.from_user.id
        payment = message.successful_payment

        # Track conversion
        if user_id in user_utm_mapping:
            utm_id = user_utm_mapping[user_id]
            track_conversion_webhook(
                utm_id=utm_id,
                customer_id=f"telegram_{user_id}",
                amount=payment.total_amount * 100,  # Convert Stars to cents
                product_name="Gold Lootbox",
                product_id=payment.invoice_payload,
                metadata={
                    "payment_method": "telegram_stars",
                    "provider_payment_charge_id": payment.provider_payment_charge_id,
                }
            )

        bot.send_message(
            message.chat.id,
            "✅ Payment successful! Your lootbox is ready!"
        )


# ============================================================================
# Database Integration (Production)
# ============================================================================

"""
In production, store UTM mappings in database instead of memory.

SQLAlchemy example:

class UserUTM(Base):
    __tablename__ = "user_utm"

    user_id = Column(BigInteger, primary_key=True)
    utm_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    converted = Column(Boolean, default=False)

def save_utm_for_user(user_id: int, utm_id: str, db: Session):
    user_utm = UserUTM(user_id=user_id, utm_id=utm_id)
    db.merge(user_utm)
    db.commit()

def get_utm_for_user(user_id: int, db: Session) -> Optional[str]:
    user_utm = db.query(UserUTM).filter(UserUTM.user_id == user_id).first()
    return user_utm.utm_id if user_utm else None
"""


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("""
🤖 Telegram Bot UTM Integration Examples

This file contains integration examples for:
1. pyTelegramBotAPI (telebot)
2. python-telegram-bot
3. Stripe payments
4. Telegram Stars payments

To use:
1. Uncomment the example you want to test
2. Set BOT_TOKEN in .env
3. Set TRACKING_API_URL in .env
4. Run: python telegram_bot_integration.py

Example:
    """)

    # Uncomment to test:
    # example_pytelegrambotapi()
    # example_python_telegram_bot()

    print("\n✅ Integration examples loaded. Read code for details.\n")
