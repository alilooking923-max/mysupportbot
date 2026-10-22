from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню для пользователя."""
    keyboard = [
        [
            InlineKeyboardButton(text="❓ Частые вопросы (FAQ)", callback_data="faq_menu"),
        ],
        [
            InlineKeyboardButton(text="✍️ Задать вопрос оператору", callback_data="contact_support"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ О нас / График работы", callback_data="about_us"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_menu_kb() -> InlineKeyboardMarkup:
    """Список вопросов в FAQ."""
    keyboard = [
        [
            InlineKeyboardButton(text="⏱ Сколько времени занимает ответ?", callback_data="faq_time"),
        ],
        [
            InlineKeyboardButton(text="💳 Вопросы по оплате / заказам", callback_data="faq_payment"),
        ],
        [
            InlineKeyboardButton(text="📁 Как прикрепить скриншот или видео?", callback_data="faq_media"),
        ],
        [
            InlineKeyboardButton(text="✍️ Написать оператору", callback_data="contact_support"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_main"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_faq_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата к списку вопросов."""
    keyboard = [
        [
            InlineKeyboardButton(text="✍️ Задать свой вопрос", callback_data="contact_support"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к вопросам", callback_data="faq_menu"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rating_kb(ticket_id: int) -> InlineKeyboardMarkup:
    """Клавиатура оценки работы поддержки (1-5 звёзд)."""
    keyboard = [
        [
            InlineKeyboardButton(text="⭐️ 1", callback_data=f"rate:{ticket_id}:1"),
            InlineKeyboardButton(text="⭐️ 2", callback_data=f"rate:{ticket_id}:2"),
            InlineKeyboardButton(text="⭐️ 3", callback_data=f"rate:{ticket_id}:3"),
            InlineKeyboardButton(text="⭐️ 4", callback_data=f"rate:{ticket_id}:4"),
            InlineKeyboardButton(text="⭐️ 5", callback_data=f"rate:{ticket_id}:5"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_operator_actions_kb(user_id: int) -> InlineKeyboardMarkup:
    """Кнопки быстрых действий для операторов под сообщением."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"op_close:{user_id}"),
            InlineKeyboardButton(text="🚫 Бан", callback_data=f"op_ban:{user_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
