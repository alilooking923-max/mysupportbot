import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import config
import database as db
import keyboards as kb

router = Router()
logger = logging.getLogger(__name__)

# Фильтр на сообщения только из чата поддержки
def is_support_chat(message: types.Message) -> bool:
    return message.chat.id == config.SUPPORT_CHAT_ID


@router.message(Command("id"))
async def cmd_get_chat_id(message: types.Message):
    """Помощник: узнать ID текущего чата."""
    await message.reply(
        f"📋 <b>ID этого чата:</b> <code>{message.chat.id}</code>\n"
        f"Скопируйте его и вставьте в <code>SUPPORT_CHAT_ID</code> в файле <code>.env</code>.",
        parse_mode="HTML"
    )


@router.message(Command("stats"), is_support_chat)
async def cmd_stats(message: types.Message):
    """Команда /stats — статистика работы поддержки."""
    stats = await db.get_statistics()
    text = (
        "📊 <b>Статистика службы поддержки:</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🎫 Всего тикетов: <b>{stats['total_tickets']}</b>\n"
        f"⏳ Открытых сейчас: <b>{stats['open_tickets']}</b>\n"
        f"⭐️ Средняя оценка: <b>{stats['avg_rating']} / 5.0</b>"
    )
    await message.reply(text, parse_mode="HTML")


@router.message(Command("ban"), is_support_chat)
async def cmd_ban(message: types.Message):
    """Команда /ban [user_id] или ответом на сообщение."""
    target_user_id = None
    args = message.text.split()
    
    if len(args) > 1 and args[1].isdigit():
        target_user_id = int(args[1])
    elif message.reply_to_message:
        target_user_id = await db.get_user_by_admin_message(message.reply_to_message.message_id)

    if not target_user_id:
        await message.reply("⚠️ Укажите ID: <code>/ban 12345678</code> или сделайте Reply на сообщение пользователя.", parse_mode="HTML")
        return

    await db.set_ban_status(target_user_id, is_banned=True)
    await message.reply(f"🚫 Пользователь <code>{target_user_id}</code> успешно заблокирован.", parse_mode="HTML")


@router.message(Command("unban"), is_support_chat)
async def cmd_unban(message: types.Message):
    """Команда /unban [user_id]."""
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        target_user_id = int(args[1])
        await db.set_ban_status(target_user_id, is_banned=False)
        await message.reply(f"✅ Пользователь <code>{target_user_id}</code> разблокирован.", parse_mode="HTML")
    else:
        await message.reply("⚠️ Формат: <code>/unban 12345678</code>", parse_mode="HTML")


@router.message(Command("close"), is_support_chat)
async def cmd_close_ticket(message: types.Message, bot: Bot):
    """Команда /close ответом на сообщение для закрытия тикета."""
    if not message.reply_to_message:
        await message.reply("⚠️ Сделайте Reply (Ответить) этой командой на сообщение пользователя, чтобы закрыть его тикет.")
        return

    user_id = await db.get_user_by_admin_message(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось найти пользователя по этому сообщению.")
        return

    ticket_id = await db.close_ticket(user_id)
    await message.reply(f"✅ Тикет #{ticket_id or ''} для пользователя <code>{user_id}</code> закрыт.", parse_mode="HTML")

    if ticket_id:
        try:
            await bot.send_message(
                chat_id=user_id,
                text="✅ <b>Ваше обращение закрыто!</b>\nПожалуйста, оцените качество работы нашего специалиста:",
                reply_markup=kb.get_rating_kb(ticket_id),
                parse_mode="HTML"
            )
        except Exception:
            pass


# --- Inline-кнопки действий оператора под тикетом ---

@router.callback_query(F.data.startswith("op_close:"))
async def cb_operator_close(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    ticket_id = await db.close_ticket(user_id)
    
    await callback.answer("Тикет закрыт!")
    await callback.message.reply(f"✅ Тикет #{ticket_id or ''} закрыт оператором {callback.from_user.full_name}.")

    if ticket_id:
        try:
            await bot.send_message(
                chat_id=user_id,
                text="✅ <b>Ваше обращение закрыто!</b>\nПожалуйста, оцените качество работы нашего специалиста:",
                reply_markup=kb.get_rating_kb(ticket_id),
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("op_ban:"))
async def cb_operator_ban(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    await db.set_ban_status(user_id, is_banned=True)
    await callback.answer("Пользователь забанен!")
    await callback.message.reply(f"🚫 Пользователь <code>{user_id}</code> заблокирован.", parse_mode="HTML")


# --- Пересылка ответа оператора пользователю через Reply ---

@router.message(is_support_chat, F.reply_to_message)
async def handle_operator_reply(message: types.Message, bot: Bot):
    # Игнорируем команды оператора (они обрабатываются хэндлерами выше)
    if message.text and message.text.startswith("/"):
        return

    replied_msg_id = message.reply_to_message.message_id
    user_id = await db.get_user_by_admin_message(replied_msg_id)

    if not user_id:
        # Сообщение не связано с клиентом (обычное общение операторов в группе)
        return

    try:
        # Отправляем копию сообщения пользователю
        await message.copy_to(chat_id=user_id)

        # Ставим реакцию или подтверждение оператору
        try:
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception:
            pass

    except TelegramForbiddenError:
        await message.reply("❌ Пользователь заблокировал бота, сообщение не доставлено.")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка отправки сообщения пользователю: {e}")
        await message.reply(f"❌ Ошибка отправки: {e.message}")
