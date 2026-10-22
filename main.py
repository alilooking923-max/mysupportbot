import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
import database as db
from handlers import user_router, operator_router

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def start_web_server():
    """Фоновый HTTP-сервер для хостингов типа Render (чтобы бот не засыпал)."""
    port_env = os.getenv("PORT")
    if not port_env:
        return None

    try:
        port = int(port_env)
        app = web.Application()

        async def ping(request):
            return web.Response(text="OK")

        app.router.add_get("/", ping)
        app.router.add_get("/health", ping)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Веб-сервер проверки здоровья запущен на порту {port}")
        return runner
    except Exception as e:
        logger.warning(f"Не удалось запустить веб-сервер: {e}")
        return None


async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN.startswith("1234567890"):
        logger.error("Запуск невозможен: укажите корректный BOT_TOKEN в файле .env!")
        return

    logger.info("Инициализация базы данных SQLite...")
    await db.init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Подключаем роутеры: операторский в приоритете, затем пользовательский
    dp.include_router(operator_router)
    dp.include_router(user_router)

    # Удаляем вебхуки и пропускаем старые накопившиеся сообщения
    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()
    logger.info(f"Бот успешно запущен: @{bot_info.username} (ID: {bot_info.id})")
    print("\n==========================================")
    print(f">> Бот @{bot_info.username} успешно запущен!")
    print("==========================================\n")

    web_runner = await start_web_server()

    try:
        await dp.start_polling(bot)
    finally:
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
