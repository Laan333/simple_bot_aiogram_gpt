"""Модели базы данных."""
from sqlalchemy import BigInteger, Column, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Message(Base):
    """Модель сообщения в диалоге."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"
