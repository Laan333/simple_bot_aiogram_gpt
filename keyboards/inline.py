"""Inline клавиатуры."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_new_request_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру с кнопкой 'Новый запрос'."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Новый запрос",
                    callback_data="new_request",
                    # Теперь официально в Bot API 9.4 — используем новые стили
                    **{"style": "primary"},   # синяя, самая заметная
                    # Возможные варианты:
                    # **{"style": "secondary"}  # сероватая
                    # **{"style": "destructive"}  # красная, «опасная»
                )
            ]
        ]
    )
    return keyboard
