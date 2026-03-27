import urllib.parse
from config import BOT_USERNAME

def calculate_final_price(original_price, in_stock, comment_type):
    multiplier = 1.1 if in_stock else 1.5
    base = int(original_price * multiplier)
    return base + 10 if comment_type == "without_ad" else base

def format_gift_info(gift_id, original_price, in_stock):
    multiplier = 1.1 if in_stock else 1.5
    final = int(original_price * multiplier)
    status = "✅ В наличии" if in_stock else "❌ Нет в наличии"
    return (
        f"**ID:** `{gift_id}`\n"
        f"**Оригинальная цена:** {original_price} ⭐️\n"
        f"**Множитель:** x{multiplier}\n"
        f"**Финальная цена:** {final} ⭐️\n"
        f"**Статус:** {status}"
    )

def format_gifts_list(gifts, page=1, total_pages=1):
    text = f"🎁 **Доступные подарки (страница {page}/{total_pages}):**\n\n"
    
    for gift_id, original_price, in_stock in gifts:
        multiplier = 1.1 if in_stock else 1.5
        final = int(original_price * multiplier)
        status = "В наличии" if in_stock else "Нет в наличии"
        status_emoji = "✅" if in_stock else "❌"
        
        text += f"{status_emoji} `{gift_id}`\n"
        text += f"  ├ Оригинал: {original_price} ⭐️\n"
        text += f"  ├ Финальная: {final} ⭐️ (x{multiplier})\n"
        text += f"  └ Статус: {status}\n\n"
    
    return text

def create_deep_link(payload=None):
    base = f"https://t.me/{BOT_USERNAME}"
    return f"{base}?start={urllib.parse.quote(payload)}" if payload else base