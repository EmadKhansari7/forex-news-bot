
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.logger import get_logger
from config.settings import DATABASE_PATH
from database.models import Base

logger = get_logger(__name__)


DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_database() -> None:

    logger.info(f"Initializing database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables are ready")


def get_session() -> Session:

    return SessionLocal()