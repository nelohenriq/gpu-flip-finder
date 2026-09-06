from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings

engine = create_engine(settings.db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from src.db.models import Base
    Base.metadata.create_all(bind=engine)
