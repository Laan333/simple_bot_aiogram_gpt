"""Конфигурация приложения."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Исключение для ошибок конфигурации."""
    pass


@dataclass
class Config:
    """Класс для хранения конфигурации."""
    
    # Telegram Bot Token
    bot_token: str
    
    # OpenAI API
    openai_api_key: str
    # Основная модель по умолчанию
    openai_model: str = "gpt-4o-mini"
    # Флаг использования "бесплатного" режима gpt-3.5 (ограничение по частоте запросов)
    free_version_gpt: bool = False
    # Строка подключения к Redis для rate limiting (если используется)
    redis_url: str = "redis://localhost:6379/0"

    # Тип базы данных: postgresql или sqlite
    db_type: str = "postgresql"
    
    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "telegram_bot"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # SQLite
    sqlite_path: str = "db.sqlite3"
    
    # Контекст диалога
    max_context_messages: int = 5
    
    def __post_init__(self) -> None:
        """Валидация конфигурации после инициализации."""
        self.validate()
    
    def validate(self) -> None:
        """Валидирует конфигурацию."""
        errors = []
        
        # Проверка обязательных полей
        if not self.bot_token or not self.bot_token.strip():
            errors.append("BOT_TOKEN не может быть пустым")
        
        if not self.openai_api_key or not self.openai_api_key.strip():
            errors.append("OPENAI_API_KEY не может быть пустым")
        
        # Проверка формата токена бота (обычно начинается с цифр и двоеточия)
        if self.bot_token and ":" not in self.bot_token:
            errors.append("BOT_TOKEN имеет неверный формат")

        # Тип БД
        allowed_db_types = {"postgresql", "sqlite"}
        if self.db_type not in allowed_db_types:
            errors.append(f"DB_TYPE должен быть одним из {allowed_db_types}, получено: {self.db_type}")
        
        # Проверка параметров PostgreSQL, только если выбран этот тип
        if self.db_type == "postgresql":
            if not (1 <= self.db_port <= 65535):
                errors.append(f"DB_PORT должен быть в диапазоне 1-65535, получено: {self.db_port}")
            if not self.db_host:
                errors.append("DB_HOST не может быть пустым при использовании PostgreSQL")
            if not self.db_name:
                errors.append("DB_NAME не может быть пустым при использовании PostgreSQL")
            if not self.db_user:
                errors.append("DB_USER не может быть пустым при использовании PostgreSQL")

        # Проверка параметров SQLite
        if self.db_type == "sqlite":
            if not self.sqlite_path or not self.sqlite_path.strip():
                errors.append("SQLITE_PATH не может быть пустым при использовании SQLite")
        
        # Проверка количества сообщений в контексте
        if self.max_context_messages < 0:
            errors.append("MAX_CONTEXT_MESSAGES не может быть отрицательным")
        if self.max_context_messages > 20:
            errors.append("MAX_CONTEXT_MESSAGES не должен превышать 20 (рекомендуется)")
        
        # Проверка модели OpenAI
        valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]
        if self.openai_model not in valid_models:
            # Не блокируем, но можно логировать предупреждение при необходимости
            pass
        
        if errors:
            error_msg = "Ошибки конфигурации:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigError(error_msg)
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Создает конфигурацию из переменных окружения.
        
        Raises:
            ConfigError: Если конфигурация невалидна
            ValueError: Если числовые значения не могут быть преобразованы
        """
        # Получаем обязательные переменные
        bot_token = os.getenv("BOT_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not bot_token:
            raise ConfigError("BOT_TOKEN не установлен в переменных окружения")
        if not openai_api_key:
            raise ConfigError("OPENAI_API_KEY не установлен в переменных окружения")

        # Тип БД
        raw_db_type = (os.getenv("DB_TYPE") or "postgresql").lower()
        if raw_db_type in {"postgres", "postgresql"}:
            db_type = "postgresql"
        elif raw_db_type in {"sqlite", "sqlite3"}:
            db_type = "sqlite"
        else:
            raise ConfigError(
                f"DB_TYPE должен быть 'postgresql' или 'sqlite', получено: {raw_db_type}"
            )
        
        # Получаем опциональные переменные с безопасным парсингом
        db_port = 5432
        if db_type == "postgresql":
            try:
                db_port = int(os.getenv("DB_PORT", "5432"))
            except ValueError:
                raise ConfigError(f"DB_PORT должен быть числом, получено: {os.getenv('DB_PORT')}")
        
        try:
            max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "5"))
        except ValueError:
            raise ConfigError(
                f"MAX_CONTEXT_MESSAGES должен быть числом, получено: {os.getenv('MAX_CONTEXT_MESSAGES')}"
            )
        
        sqlite_path = os.getenv("SQLITE_PATH", "db.sqlite3").strip()

        # FREE_VERSION_GPT (true/false)
        raw_free = (os.getenv("FREE_VERSION_GPT") or "false").strip().lower()
        free_version_gpt = raw_free in {"1", "true", "yes", "y"}

        # REDIS_URL (опционально)
        redis_url = (os.getenv("REDIS_URL") or "redis://localhost:6379/0").strip()
        
        return cls(
            bot_token=bot_token.strip(),
            openai_api_key=openai_api_key.strip(),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            db_type=db_type,
            db_host=os.getenv("DB_HOST", "localhost").strip(),
            db_port=db_port,
            db_name=os.getenv("DB_NAME", "telegram_bot").strip(),
            db_user=os.getenv("DB_USER", "postgres").strip(),
            db_password=os.getenv("DB_PASSWORD", "postgres"),
            sqlite_path=sqlite_path,
            free_version_gpt=free_version_gpt,
            max_context_messages=max_context_messages,
            redis_url=redis_url,
        )
    
    def __repr__(self) -> str:
        """Безопасное представление конфигурации без чувствительных данных."""
        return (
            f"Config("
            f"bot_token={'***' if self.bot_token else 'None'}, "
            f"openai_api_key={'***' if self.openai_api_key else 'None'}, "
            f"openai_model={self.openai_model}, "
            f"db_type={self.db_type}, "
            f"db_host={self.db_host if self.db_type == 'postgresql' else '-'}, "
            f"db_port={self.db_port if self.db_type == 'postgresql' else '-'}, "
            f"db_name={self.db_name if self.db_type == 'postgresql' else '-'}, "
            f"db_user={self.db_user if self.db_type == 'postgresql' else '-'}, "
            f"sqlite_path={self.sqlite_path if self.db_type == 'sqlite' else '-'}, "
            f"db_password={'***' if self.db_password else 'None'}, "
            f"max_context_messages={self.max_context_messages}"
            f")"
        )
    
    def get_db_url(self) -> str:
        """Возвращает sync URL для подключения к базе данных."""
        if self.db_type == "postgresql":
            return (
                f"postgresql://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )
        # SQLite
        return f"sqlite:///{self.sqlite_path}"
    
    def get_async_db_url(self) -> str:
        """Возвращает async URL для подключения к базе данных."""
        if self.db_type == "postgresql":
            return (
                f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )
        # SQLite
        return f"sqlite+aiosqlite:///{self.sqlite_path}"
