"""Обработчики команд."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.connection import get_session
from database.repository import MessageRepository
from keyboards.inline import get_new_request_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    async for session in get_session():
        repo = MessageRepository(session)
        # Удаляем все предыдущие сообщения пользователя
        deleted_count = await repo.delete_user_messages(message.from_user.id)
        
        welcome_text = (
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            "Я бот с искусственным интеллектом, основанным на ChatGPT.\n"
            "Просто отправь мне любое сообщение, и я отвечу!\n\n"
            "Доступные команды:\n"
            "/help - показать справку\n"
            "/start - начать новый диалог"
        )
        
        if deleted_count > 0:
            welcome_text += f"\n\n✅ История диалога очищена ({deleted_count} сообщений)"
        
        await message.answer(
            welcome_text,
            reply_markup=get_new_request_keyboard()
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help."""
    help_text = (
        "📖 Справка по использованию бота:\n\n"
        "🔹 Просто отправь мне любое текстовое сообщение, и я отвечу на него!\n\n"
        "🔹 Бот запоминает контекст последних 5 сообщений для более качественных ответов.\n\n"
        "🔹 Доступные команды:\n"
        "  /start - начать новый диалог (очистить историю)\n"
        "  /help - показать эту справку\n\n"
        "🔹 Кнопка 'Новый запрос' также очищает историю диалога.\n\n"
        "💡 Совет: Используй контекст для более естественного общения!"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_new_request_keyboard()
    )
