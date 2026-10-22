import os
import sys
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPPORT_CHAT_ID_RAW = os.getenv("SUPPORT_CHAT_ID", "0").strip()

if not BOT_TOKEN or BOT_TOKEN == "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ":
    print("\n[!] ОШИБКА: Укажите реальный BOT_TOKEN в файле .env!")
    print("Получите токен у официального бота @BotFather в Telegram.\n")

try:
    SUPPORT_CHAT_ID = int(SUPPORT_CHAT_ID_RAW)
except ValueError:
    SUPPORT_CHAT_ID = 0

WELCOME_MESSAGE = os.getenv(
    "WELCOME_MESSAGE",
    "👋 <b>Добро пожаловать в службу поддержки!</b>\n\n"
    "Вы можете изучить частые вопросы в меню ниже или сразу задать свой вопрос — "
    "наши операторы ответят вам прямо в этом диалоге."
)
