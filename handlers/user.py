import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

import config
import database as db
import keyboards as kb

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: types.Message):
    """Команда /start — регистрация и главное меню."""
    user = message.from_user
    await db.get_or_create_user(user.id, user.username, user.full_name)

    if await db.is_user_banned(user.id):
        await message.answer("🚫 Вы заблокированы и не можете отправлять сообщения в поддержку.")
        return

    await message.answer(
        config.WELCOME_MESSAGE,
        reply_markup=kb.get_main_menu_kb(),
        parse_mode="HTML"
    )


async def safe_edit_text(message: types.Message, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise


# --- Обработка FAQ и навигации меню ---

@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: types.CallbackQuery):
    await safe_edit_text(
        callback.message,
        config.WELCOME_MESSAGE,
        reply_markup=kb.get_main_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data == "faq_menu")
async def cb_faq_menu(callback: types.CallbackQuery):
    text = (
        "❓ <b>Часто задаваемые вопросы:</b>\n\n"
        "Выберите интересующий вас вопрос ниже. Если не нашли ответ — "
        "нажмите «Написать оператору»."
    )
    await safe_edit_text(callback.message, text, reply_markup=kb.get_faq_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "faq_time")
async def cb_faq_time(callback: types.CallbackQuery):
    text = (
        "⏱ <b>Сколько времени занимает ответ?</b>\n\n"
        "Обычно наши специалисты отвечают в течение <b>5–15 минут</b>.\n"
        "В ночное время или часы пиковой нагрузки время ответа может быть немного увеличено."
    )
    await safe_edit_text(callback.message, text, reply_markup=kb.get_back_to_faq_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "faq_payment")
async def cb_faq_payment(callback: types.CallbackQuery):
    text = (
        "💳 <b>Вопросы по оплате и заказам</b>\n\n"
        "Если у вас возникли сложности с оплатой, не поступил платёж или нужна квитанция — "
        "пожалуйста, отправьте квитанцию или номер транзакции прямо в этот чат оператору."
    )
    await safe_edit_text(callback.message, text, reply_markup=kb.get_back_to_faq_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "faq_media")
async def cb_faq_media(callback: types.CallbackQuery):
    text = (
        "📁 <b>Как отправить скриншот или файл?</b>\n\n"
        "Бот поддерживает любые медиафайлы: скриншоты, видео, голосовые сообщения и документы. "
        "Просто отправьте их в чат, как обычному контакту."
    )
    await safe_edit_text(callback.message, text, reply_markup=kb.get_back_to_faq_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "about_us")
async def cb_about_us(callback: types.CallbackQuery):
    text = (
        "ℹ️ <b>О службе поддержки</b>\n\n"
        "Мы заботимся о том, чтобы каждый вопрос был решен быстро и качественно.\n"
        "🕒 <b>График работы:</b> Ежедневно с 10:00 до 23:00 (МСК).\n"
        "Чтобы начать диалог, просто отправьте сообщение в чат."
    )
    await safe_edit_text(callback.message, text, reply_markup=kb.get_main_menu_kb(), parse_mode="HTML")
    await callback.answer()



@router.callback_query(F.data == "contact_support")
async def cb_contact_support(callback: types.CallbackQuery):
    text = (
        "✍️ <b>Напишите ваш вопрос:</b>\n\n"
        "Опишите ситуацию максимально подробно одним сообщением (можно прикрепить фото или видео). "
        "Первый свободный оператор ответит вам здесь."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# --- Оценка обслуживания ---

@router.callback_query(F.data.startswith("rate:"))
async def cb_rate(callback: types.CallbackQuery):
    _, ticket_id_str, rating_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    rating = int(rating_str)

    await db.set_ticket_rating(ticket_id, rating)
    stars = "⭐️" * rating
    await callback.message.edit_text(
        f"🙏 <b>Спасибо за вашу оценку ({stars})!</b>\n"
        f"Ваш отзыв помогает нам становиться лучше.",
        parse_mode="HTML"
    )
    await callback.answer("Спасибо за обратную связь!")


# --- Приём сообщений от пользователя в ЛС ---

@router.message(F.chat.type == "private")
async def handle_user_incoming_message(message: types.Message, bot: Bot):
    user = message.from_user
    await db.get_or_create_user(user.id, user.username, user.full_name)

    # Проверка на бан
    if await db.is_user_banned(user.id):
        await message.answer("🚫 Вы заблокированы и не можете отправлять сообщения в поддержку.")
        return

    # Проверка ID чата поддержки
    if not config.SUPPORT_CHAT_ID or config.SUPPORT_CHAT_ID == -1001234567890:
        await message.answer(
            "⚠️ <b>Чат операторов поддержки ещё не привязан!</b>\n\n"
            "Если вы администратор:\n"
            "1. Создайте группу для операторов в Telegram\n"
            "2. Добавьте в неё этого бота и сделайте администратором\n"
            "3. Отправьте в группе команду <code>/id</code> и укажите этот ID в файле <code>.env</code>.",
            parse_mode="HTML"
        )
        return


    # Создаём или получаем тикет
    ticket_id = await db.get_or_create_ticket(user.id)

    user_link = f"@{user.username}" if user.username else f"ID: {user.id}"
    header_text = (
        f"📩 <b>Новое обращение (Тикет #{ticket_id})</b>\n"
        f"👤 <b>От:</b> {user.full_name} ({user_link})\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"<i>💡 Для ответа сделайте Reply (Ответить) на сообщение ниже.</i>"
    )

    try:
        # Отправляем информационный блок операторам
        info_msg = await bot.send_message(
            chat_id=config.SUPPORT_CHAT_ID,
            text=header_text,
            reply_markup=kb.get_operator_actions_kb(user.id),
            parse_mode="HTML"
        )
        await db.save_message_link(info_msg.message_id, user.id, message.message_id)

        # Пересылаем саму копию сообщения (текст, фото, видео, голосовое и т.д.)
        copied_msg = await message.copy_to(chat_id=config.SUPPORT_CHAT_ID)
        await db.save_message_link(copied_msg.message_id, user.id, message.message_id)

        # Подтверждение пользователю
        await message.answer("⏳ <b>Сообщение отправлено!</b> Оператор скоро вам ответит.", parse_mode="HTML")

    except TelegramBadRequest as e:
        logger.error(f"Ошибка отправки в чат операторов: {e}")
        await message.answer("❌ Произошла ошибка при передаче сообщения. Попробуйте позже.")
