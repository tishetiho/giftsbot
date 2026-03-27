from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Список подарков"), KeyboardButton(text="💰 Купить")],
        [KeyboardButton(text="📦 Мои покупки"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить подарок")],
        [KeyboardButton(text="🗑 Удалить подарок")],
        [KeyboardButton(text="📋 Все подарки (админ)")],
        [KeyboardButton(text="◀️ Назад")]
    ],
    resize_keyboard=True
)

def gifts_list_keyboard(gifts):
    kb = []
    for gift_id, price, in_stock in gifts:
        status = "✅" if in_stock else "❌"
        kb.append([InlineKeyboardButton(
            text=f"{status} {gift_id[:8]}... ({price}⭐️) Купить",
            callback_data=f"buy_{gift_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=kb)

anonymous_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👤 Открыто", callback_data="anon_no")],
        [InlineKeyboardButton(text="🕵️ Анонимно", callback_data="anon_yes")]
    ]
)

comment_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 С рекламой (0⭐️)", callback_data="comment_with_ad")],
        [InlineKeyboardButton(text="💬 Без рекламы (+10⭐️)", callback_data="comment_without_ad")],
        [InlineKeyboardButton(text="🔇 Без комментария", callback_data="comment_no")]
    ]
)

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_no")]
    ]
)

payment_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оплатить Stars", pay=True)]
    ]
)

def admin_confirm_delivery_kb(purchase_payload):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Подарок отправлен", 
                callback_data=f"delivered_{purchase_payload}"
            )]
        ]
    )
