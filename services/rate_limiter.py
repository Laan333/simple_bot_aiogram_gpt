"""Сервис для ограничения частоты запросов (rate limiting) с использованием Redis."""
from __future__ import annotations

from typing import Optional, Tuple

from redis.asyncio import Redis

from config import Config

_redis_client: Optional[Redis] = None


def _get_redis_dsn(config: Config) -> str:
    """Возвращает DSN для подключения к Redis."""
    # Можно расширить до отдельных переменных (REDIS_HOST/PORT/DB), пока используем REDIS_URL
    return getattr(config, "redis_url", "redis://localhost:6379/0")


def get_redis_client(config: Config) -> Redis:
    """Лениво инициализирует и возвращает глобальный Redis-клиент."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(_get_redis_dsn(config), decode_responses=True)
    return _redis_client


class RateLimiter:
    """Простой rate-limiter: не более одного запроса на пользователя за указанный период."""

    def __init__(self, redis: Redis, prefix: str = "rate_limit", ttl_seconds: int = 180) -> None:
        """
        Args:
            redis: Async Redis client
            prefix: Префикс ключей в Redis
            ttl_seconds: Время жизни ключа в секундах (по умолчанию: 180 = 3 минуты)
        """
        self.redis = redis
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def _key(self, user_id: int) -> str:
        return f"{self.prefix}:user:{user_id}"

    async def get_limit_state(self, user_id: int) -> Tuple[bool, int]:
        """
        Проверяет, ограничен ли сейчас пользователь по частоте.

        Returns:
            limited: True, если пользователь в "cooldown"
            retry_after: Сколько секунд ждать до следующего запроса (0, если не ограничен)
        """
        key = self._key(user_id)
        ttl = await self.redis.ttl(key)
        if ttl is not None and ttl > 0:
            return True, ttl
        return False, 0

    async def touch(self, user_id: int) -> None:
        """
        Помечает пользователя как использовавшего лимит на текущий период.
        Вызывается только после успешного запроса к ИИ.
        """
        key = self._key(user_id)
        # setex перезапишет ключ и обновит TTL
        await self.redis.setex(key, self.ttl_seconds, "1")

