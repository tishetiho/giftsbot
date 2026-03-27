import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from config import BOT_USERNAME, ADMIN_IDS
from database import *
from keyboards import *
from states import BuyGift, AdminStates
from utils import calculate_final_price, format_gift_info, format_gifts_list, create_deep_link

router = Router()

async def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(Command("start"))
async def cmd_start(message):
    user = message.from_user
    add_user(user.id, user.username, user.first_name)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("gift_"):
        gift_id = args[1][5:]
        await message.answer(f"🔗 Вы перешли по ссылке на подарок {gift_id[:8]}...")
    
    await message.answer(f"👋 Добро пожаловать, {user.first_name}!", reply_markup=main_menu)
# сделал xegori (aka rmontero -> rm)
@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message):
    text = (
        "**🎁 Как купить подарок:**\n"
        "1. Нажмите 'Купить' в меню\n"
        "2. Введите ID подарка\n"
        "3. Укажите получателя (ID или 'me')\n"
        "4. Выберите анонимность\n"
        "5. Выберите комментарий\n"
        "6. Подтвердите и оплатите\n\n"
        "**💰 Цены:**\n"
        "- В наличии: x1.1 от цены\n"
        "- Нет в наличии: x1.5 от цены\n"
        "- Без рекламы: +10⭐️\n\n"
        "**📋 Команды:**\n"
        "/start - Главное меню\n"
        "/gifts - Список подарков\n"
        "/stats - Моя статистика\n"
        "/admin - Админ панель"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message):
    user_id = message.from_user.id
    purchases = get_user_purchases(user_id)
    
    if not purchases:
        await message.answer("📭 У вас пока нет покупок.")
        return
    
    total = sum(p[5] for p in purchases)
    text = f"**📊 Статистика:**\n"
    text += f"Покупок: {len(purchases)}\n"
    text += f"Потрачено: {total}⭐️\n\n"
    text += "**Последние:**\n"
    
    for p in purchases[:5]:
        gift_id, recipient, anon, _, _, price, date = p
        who = "себе" if recipient == user_id else f"пользователю {recipient}"
        text += f"• {gift_id[:8]}... ({who}) - {price}⭐️\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("gifts"))
@router.message(F.text == "🎁 Список подарков")
async def cmd_gifts(message):
    gifts = get_all_gifts()
    if not gifts:
        await message.answer("📭 Список подарков пуст.")
        return
    
    await show_gifts_page(message, gifts, 1)

async def show_gifts_page(message, gifts, page):
    page_size = 4
    total_pages = (len(gifts) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    page_gifts = gifts[start:end]
    
    text = format_gifts_list(page_gifts, page, total_pages)
    
    kb = []
    
    for gift_id, price, in_stock in page_gifts:
        status = "✅" if in_stock else "❌"
        kb.append([InlineKeyboardButton(
            text=f"{status} {gift_id[:8]}... ({price}⭐️) Купить",
            callback_data=f"buy_{gift_id}"
        )])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"page_{page+1}"))
    
    if nav_buttons:
        kb.append(nav_buttons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data.startswith("page_"))
async def process_pagination(callback):
    page = int(callback.data.split("_")[1])
    gifts = get_all_gifts()
    
    page_size = 4
    total_pages = (len(gifts) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    page_gifts = gifts[start:end]
    
    text = format_gifts_list(page_gifts, page, total_pages)
    
    kb = []
    
    for gift_id, price, in_stock in page_gifts:
        status = "✅" if in_stock else "❌"
        kb.append([InlineKeyboardButton(
            text=f"{status} {gift_id[:8]}... ({price}⭐️) Купить",
            callback_data=f"buy_{gift_id}"
        )])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"page_{page+1}"))
    
    if nav_buttons:
        kb.append(nav_buttons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def process_buy_callback(callback, state):
    gift_id = callback.data[4:]
    gift = get_gift(gift_id)
    
    if not gift:
        await callback.answer("❌ Подарок не найден.", show_alert=True)
        return
    
    await state.update_data(gift_id=gift_id, original_price=gift[1], in_stock=gift[2])
    await state.set_state(BuyGift.waiting_for_recipient)
    
    link = create_deep_link(f"gift_{gift_id}")
    await callback.message.answer(
        f"{format_gift_info(gift_id, gift[1], gift[2])}\n\n"
        f"🔗 Ссылка:\n`{link}`\n\n"
        "👤 Введите ID получателя (или 'me' для себя):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(F.text == "💰 Купить")
async def buy_start(message, state):
    await state.set_state(BuyGift.waiting_for_gift_id)
    await message.answer("🔍 Введите ID подарка из списка выше:")

@router.message(BuyGift.waiting_for_gift_id)
async def process_gift_id(message, state):
    gift_id = message.text.strip()
    gift = get_gift(gift_id)
    
    if not gift:
        await message.answer("❌ Подарок не найден.")
        return
    
    await state.update_data(gift_id=gift_id, original_price=gift[1], in_stock=gift[2])
    await state.set_state(BuyGift.waiting_for_recipient)
    
    link = create_deep_link(f"gift_{gift_id}")
    await message.answer(
        f"{format_gift_info(gift_id, gift[1], gift[2])}\n\n"
        f"🔗 Ссылка:\n`{link}`\n\n"
        "👤 Введите ID получателя (или 'me' для себя):",
        parse_mode="Markdown"
    )

@router.message(BuyGift.waiting_for_recipient)
async def process_recipient(message, state):
    text = message.text.strip().lower()
    
    if text == "me":
        recipient = message.from_user.id
    elif text.isdigit():
        recipient = int(text)
    else:
        await message.answer("❌ Неверный формат.")
        return
    
    await state.update_data(recipient_id=recipient)
    await state.set_state(BuyGift.waiting_for_anonymous)
    await message.answer("👤 Выберите тип отправки:", reply_markup=anonymous_keyboard)

@router.callback_query(BuyGift.waiting_for_anonymous)
async def process_anonymous(callback, state):
    anon = callback.data == "anon_yes"
    await state.update_data(anonymous=anon)
    await state.set_state(BuyGift.waiting_for_comment)
    await callback.message.edit_text("💬 Выберите комментарий:", reply_markup=comment_keyboard)
    await callback.answer()

@router.callback_query(BuyGift.waiting_for_comment)
async def process_comment(callback, state):
    comment_type = callback.data
    
    if comment_type == "comment_without_ad":
        await state.update_data(comment_type=comment_type)
        await state.set_state(BuyGift.waiting_for_custom_comment)
        await callback.message.edit_text("✏️ Напишите ваш комментарий (макс. 200 символов):")
    else:
        await state.update_data(comment_type=comment_type, custom_comment="")
        await show_confirmation(callback.message, state)
    await callback.answer()

@router.message(BuyGift.waiting_for_custom_comment)
async def process_custom_comment(message, state):
    if len(message.text) > 200:
        await message.answer("❌ Слишком длинный комментарий.")
        return
    
    await state.update_data(custom_comment=message.text)
    await show_confirmation(message, state)

async def show_confirmation(message, state):
    data = await state.get_data()
    
    final_price = calculate_final_price(data['original_price'], data['in_stock'], data['comment_type'])
    await state.update_data(final_price=final_price)
    await state.set_state(BuyGift.waiting_for_confirmation)
    
    who = "себе" if data['recipient_id'] == message.from_user.id else f"пользователю {data['recipient_id']}"
    
    text = (
        f"**📝 Подтверждение покупки**\n\n"
        f"🎁 Подарок: `{data['gift_id'][:8]}...`\n"
        f"👤 Получатель: {who}\n"
        f"🕵️ Анонимно: {'Да' if data['anonymous'] else 'Нет'}\n"
        f"💬 Комментарий: {data.get('custom_comment', 'Нет')[:30]}\n"
        f"💰 Цена: {final_price} ⭐️\n\n"
        f"**ИТОГО: {final_price} ⭐️**"
    )
    
    await message.answer(text, parse_mode="Markdown", reply_markup=confirm_keyboard)

@router.callback_query(BuyGift.waiting_for_confirmation, F.data == "confirm_yes")
async def process_confirm(callback, state):
    data = await state.get_data()
    payload = str(uuid.uuid4())
    
    add_pending_purchase(
        payload=payload,
        user_id=callback.from_user.id,
        gift_id=data['gift_id'],
        recipient_id=data['recipient_id'],
        anonymous=data['anonymous'],
        comment_type=data['comment_type'],
        custom_comment=data.get('custom_comment', ''),
        final_price=data['final_price']
    )
    
    prices = [LabeledPrice(label="Подарок", amount=data['final_price'])]
    
    await callback.message.answer_invoice(
        title="Покупка подарка",
        description=f"Подарок {data['gift_id'][:8]}...",
        payload=payload,
        currency="XTR",
        prices=prices,
        reply_markup=payment_keyboard
    )
    
    await state.clear()
    await callback.answer()

@router.callback_query(BuyGift.waiting_for_confirmation, F.data == "confirm_no")
async def process_cancel(callback, state):
    await state.clear()
    await callback.message.edit_text("❌ Покупка отменена.")
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_q):
    await pre_checkout_q.answer(ok=True)

@router.message(F.successful_payment)
async def process_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    pending = get_pending_purchase(payload)
    
    if pending:
        # Сохраняем в основную базу
        add_purchase(
            pending.user_id, pending.gift_id, pending.recipient_id,
            pending.anonymous, pending.comment_type, pending.custom_comment,
            pending.final_price, message.successful_payment.total_amount, payload
        )
        
        # Информируем пользователя
        await message.answer(
            "✅ **Оплата принята!**\n"
            "Ваш заказ передан администратору. Подарок будет доставлен в ближайшее время."
        )

        # Оповещаем админов
        admin_text = (
            f"💰 **Новая покупка!**\n\n"
            f"👤 **Отправитель:** `{pending.user_id}`\n"
            f"🎯 **Получатель:** `{pending.recipient_id}`\n"
            f"🎁 **ID подарка:** `{pending.gift_id}`\n"
            f"💬 **Комментарий:** {pending.custom_comment or 'Нет'}\n"
            f"🕵️ **Анонимно:** {'Да' if pending.anonymous else 'Нет'}"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id, 
                    admin_text, 
                    reply_markup=admin_confirm_delivery_kb(payload),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки админу {admin_id}: {e}")
        
        # Удаляем из временной таблицы
        delete_pending_purchase(payload)

@router.callback_query(F.data.startswith("delivered_"))
async def admin_delivery_confirmed(callback: CallbackQuery):
    # Извлекаем payload из callback_data
    payload = callback.data.split("_")[1]
    
    # Можно вытащить данные о покупке из БД, чтобы знать кому писать
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, recipient_id, anonymous FROM purchases WHERE payment_payload = ?", (payload,))
    res = cur.fetchone()
    conn.close()

    if res:
        user_id, recipient_id, anonymous = res
        
        # Уведомляем отправителя
        try:
            await callback.bot.send_message(user_id, "🎁 Ваш подарок успешно доставлен получателю!")
        except:
            pass
            
        # Уведомляем получателя (если это не сам отправитель)
        if recipient_id and int(recipient_id) != user_id:
            try:
                from_user = "Анонима" if anonymous else f"пользователя id`{user_id}`"
                await callback.bot.send_message(
                    recipient_id, 
                    f"🎁 Привет! Тебе пришел подарок от {from_user}!"
                )
            except:
                pass

    await callback.message.edit_text(callback.message.text + "\n\n✅ **ОТПРАВЛЕНО**")
    await callback.answer("Уведомления отправлены!")

@router.message(Command("admin"))
async def cmd_admin(message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer("👨‍💻 Панель администратора", reply_markup=admin_menu)

@router.message(F.text == "➕ Добавить подарок")
async def admin_add_prompt(message, state):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_gift_add)
    await message.answer("Введите ID и цену через пробел:")

@router.message(AdminStates.waiting_for_gift_add)
async def admin_add_execute(message, state):
    if not await is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❌ Неверный формат.")
        return
    
    gift_id, price = parts[0], int(parts[1])
    add_gift(gift_id, price, True)
    
    link = create_deep_link(f"gift_{gift_id}")
    await message.answer(f"✅ Подарок добавлен!\n\n🔗 Ссылка:\n`{link}`", parse_mode="Markdown")
    await state.clear()

@router.message(F.text == "🗑 Удалить подарок")
async def admin_remove_prompt(message, state):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_gift_remove)
    await message.answer("Введите ID подарка:")

@router.message(AdminStates.waiting_for_gift_remove)
async def admin_remove_execute(message, state):
    if not await is_admin(message.from_user.id):
        return
    
    gift_id = message.text.strip()
    delete_gift(gift_id)
    await message.answer(f"✅ Подарок удалён.")
    await state.clear()

@router.message(F.text == "📋 Все подарки (админ)")
async def admin_list(message):
    if not await is_admin(message.from_user.id):
        return
    
    gifts = get_all_gifts()
    if not gifts:
        await message.answer("📭 Список подарков пуст.")
        return
    
    text = "**📋 Все подарки:**\n\n"
    for gid, price, stock in gifts:
        status = "✅" if stock else "❌"
        link = create_deep_link(f"gift_{gid}")
        text += f"{status} `{gid[:8]}...` - {price}⭐️\n🔗 `{link}`\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "◀️ Назад")
async def admin_back(message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("Главное меню", reply_markup=main_menu)

@router.message(Command("cancel"))
async def cmd_cancel(message, state):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного действия.", reply_markup=main_menu)
        return
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=main_menu)
