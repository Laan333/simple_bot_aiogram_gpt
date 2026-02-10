"""Репозиторий для работы с сообщениями."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message


class MessageRepository:
    """Репозиторий для работы с сообщениями."""
    
    def __init__(self, session: AsyncSession):
        """Инициализирует репозиторий."""
        self.session = session
    
    async def create_message(
        self,
        user_id: int,
        message_text: str,
        response_text: Optional[str] = None,
    ) -> Message:
        """Создает новое сообщение."""
        message = Message(
            user_id=user_id,
            message_text=message_text,
            response_text=response_text,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_recent_messages(
        self,
        user_id: int,
        limit: int = 5,
    ) -> List[Message]:
        """Получает последние сообщения пользователя."""
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        # Возвращаем в хронологическом порядке (старые -> новые)
        return list(reversed(messages))
    
    async def delete_user_messages(self, user_id: int) -> int:
        """Удаляет все сообщения пользователя."""
        stmt = select(Message).where(Message.user_id == user_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        count = len(messages)
        for message in messages:
            await self.session.delete(message)
        
        await self.session.commit()
        return count
