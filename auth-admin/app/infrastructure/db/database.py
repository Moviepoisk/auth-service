from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

Base = declarative_base()

# Создаем синхронный движок SQLAlchemy
engine = create_engine(
    str(settings.database_url),  # Убедитесь, что settings.database_url указывает на вашу синхронную БД
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_session() -> Iterator[Session]:
    """Генератор сессий SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()