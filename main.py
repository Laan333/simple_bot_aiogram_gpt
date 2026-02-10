"""Главный файл для запуска бота."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config, ConfigError
from database.connection import close_db, init_db
from handlers import commands, messages

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

 
async def main() -> None:
    """Главная функция для запуска бота."""
    # Загружаем и валидируем конфигурацию
    try:
        config = Config.from_env()
        logger.info("Конфигурация загружена и валидирована успешно")
    except ConfigError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке конфигурации: {e}")
        sys.exit(1)
    
    # Инициализируем базу данных
    logger.info("Инициализация базы данных...")
    try:
        await init_db(config)
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        sys.exit(1)
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot, config=config)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
