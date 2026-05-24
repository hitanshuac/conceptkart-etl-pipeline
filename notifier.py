import os
import requests

def notify_price_drop(product_name: str, price: int, url: str):
    """
    Triggers a Telegram notification when the target price is hit.
    Expects TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment.
    """
    title = "🎉 Target Price Hit!"
    message = f"<b>{title}</b>\n\n{product_name} is now Rs.{price}!\n<a href='{url}'>Buy it here</a>"
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        fallback_title = "Target Price Hit!"
        print(f"NOTIFYING (Terminal Fallback): {fallback_title} - {product_name} is now Rs.{price}! Buy it here: {url}")
        print("WARNING: Telegram credentials not found. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return
        
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        print("SUCCESS: Telegram notification dispatched.")
    except Exception as e:
        print(f"FAILED: Could not send Telegram notification: {e}")

if __name__ == "__main__":
    notify_price_drop("Test Product", 999, "http://example.com")
