from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import Base


def create_sqlalchemy_engine(settings: Settings):
    connect_args = {}
    if settings.rank_proxy_database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.rank_proxy_database_url, connect_args=connect_args)


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = create_sqlalchemy_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(settings: Settings) -> None:
    settings.ensure_database_parent()
    engine = create_sqlalchemy_engine(settings)
    Base.metadata.create_all(bind=engine)


def check_db(settings: Settings) -> bool:
    engine = create_sqlalchemy_engine(settings)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def session_dependency(session_factory: sessionmaker[Session]):
    def _get_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return _get_session
