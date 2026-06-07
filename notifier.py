"""
Multi-channel notification system.

Sends alerts when target prices are hit. Supports:
  - Telegram Bot (existing)
  - Generic webhook (Slack, Discord, or custom endpoints)

All notification channels are optional and configured via environment
variables (12-Factor compliant). Failure to notify never crashes the pipeline.
"""

import os

import requests


def notify_price_drop(product_name: str, price: int, url: str):
    """Dispatch price drop notifications across all configured channels.

    Expects environment variables:
    - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID: Telegram notifications
    - WEBHOOK_URL: Generic webhook (Slack, Discord, etc.)
    """
    title = "Target Price Hit!"

    # Channel 1: Telegram
    _notify_telegram(product_name, price, url, title)

    # Channel 2: Generic Webhook
    _notify_webhook(product_name, price, url, title)


def _notify_telegram(product_name: str, price: int, url: str, title: str):
    """Send a Telegram notification."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print(f"NOTIFYING (Terminal Fallback): {title} - {product_name} is now Rs.{price}! Buy: {url}")
        print("WARNING: Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return

    # Use plain text to avoid Windows charmap encoding issues with emojis
    message = f"<b>{title}</b>\n\n{product_name} is now Rs.{price}!\n<a href='{url}'>Buy it here</a>"

    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        print("SUCCESS: Telegram notification dispatched.")
    except Exception as e:
        print(f"FAILED: Could not send Telegram notification: {e}")


def _notify_webhook(product_name: str, price: int, url: str, title: str):
    """Send a notification to a generic webhook endpoint.

    The payload format is compatible with Slack, Discord, and
    most webhook-based notification services.
    """
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        return  # Silently skip if not configured

    payload = {
        "text": f"*{title}*\n{product_name} is now Rs.{price}!\n{url}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n{product_name} is now Rs.{price}!\n<{url}|Buy it here>",
                },
            }
        ],
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        print("SUCCESS: Webhook notification dispatched.")
    except Exception as e:
        print(f"FAILED: Could not send webhook notification: {e}")


if __name__ == "__main__":
    notify_price_drop("Test Product", 999, "http://example.com")
