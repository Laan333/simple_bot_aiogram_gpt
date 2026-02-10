"""Обработчики текстовых сообщений."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from redis.exceptions import ConnectionError as RedisConnectionError

from config import Config
from database.connection import get_session
from database.repository import MessageRepository
from keyboards.inline import get_new_request_keyboard
from services.chatgpt import ChatGPTService
from services.rate_limiter import get_redis_client, RateLimiter

router = Router()


@router.message()
async def handle_message(message: Message, config: Config) -> None:
    """Обработчик текстовых сообщений."""
    if not message.text:
        await message.answer("Пожалуйста, отправь текстовое сообщение.")
        return

    # Ограничение частоты запросов в "бесплатном" режиме gpt-3.5-turbo
    limiter: RateLimiter | None = None
    if config.free_version_gpt and config.openai_model == "gpt-3.5-turbo":
        try:
            redis = get_redis_client(config)
            limiter = RateLimiter(redis, prefix="rate_limit:gpt35", ttl_seconds=180)
            # На этом этапе только проверяем, в лимите ли пользователь,
            # но НЕ записываем его в Redis.
            limited, retry_after = await limiter.get_limit_state(message.from_user.id)
            if limited:
                minutes = retry_after // 60
                seconds = retry_after % 60
                wait_str = f"{minutes} мин {seconds} сек" if minutes else f"{seconds} сек"
                await message.answer(
                    "⚠️ В бесплатном режиме gpt-3.5-turbo можно отправлять не более одного запроса "
                    "раз в 3 минуты.\n"
                    f"Пожалуйста, подожди ещё приблизительно {wait_str} и попробуй снова."
                )
                return
        except RedisConnectionError:
            # Если Redis недоступен, просто отключаем лимит и продолжаем работу,
            # чтобы бот не падал из-за отсутствия Redis.
            limiter = None

    # Показываем индикатор печати
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    async for session in get_session():
        repo = MessageRepository(session)
        chatgpt_service = ChatGPTService(config)
        
        try:
            # Получаем последние сообщения для контекста
            # Берем max_context_messages, но исключаем текущее сообщение
            recent_messages = await repo.get_recent_messages(
                user_id=message.from_user.id,
                limit=config.max_context_messages,
            )
            
            # Форматируем контекст для ChatGPT
            context_messages = chatgpt_service.format_context_messages(recent_messages)
            
            # Генерируем ответ
            response = await chatgpt_service.generate_response(
                user_message=message.text,
                context_messages=context_messages if context_messages else None,
            )
            
            # Сохраняем сообщение и ответ в БД
            await repo.create_message(
                user_id=message.from_user.id,
                message_text=message.text,
                response_text=response,
            )

            # Фиксируем использование лимита ТОЛЬКО после успешного ответа ИИ
            if limiter is not None and config.free_version_gpt and config.openai_model == "gpt-3.5-turbo":
                try:
                    await limiter.touch(message.from_user.id)
                except RedisConnectionError:
                    # Если Redis отвалился в этот момент — просто игнорируем
                    pass
            
            # Отправляем ответ пользователю
            await message.answer(
                response,
                reply_markup=get_new_request_keyboard()
            )
        
        except Exception as e:
            error_message = (
                f"❌ Произошла ошибка при обработке запроса:\n"
                f"{str(e)}\n\n"
                f"Попробуй еще раз или используй /start для начала нового диалога."
            )
            await message.answer(error_message)


@router.callback_query(F.data == "new_request")
async def handle_new_request(callback: CallbackQuery, config: Config) -> None:
    """Обработчик кнопки 'Новый запрос'."""
    async for session in get_session():
        repo = MessageRepository(session)
        
        # Удаляем все сообщения пользователя
        deleted_count = await repo.delete_user_messages(callback.from_user.id)
        
        response_text = (
            "✅ История диалога очищена!\n\n"
            "Можешь начать новый диалог. Просто отправь мне сообщение."
        )
        
        if deleted_count > 0:
            response_text += f"\n\nУдалено сообщений: {deleted_count}"
        else:
            response_text += "\n\nИстория была пуста."
        
        await callback.message.edit_text(
            response_text,
            reply_markup=get_new_request_keyboard()
        )
        await callback.answer("История диалога очищена")
