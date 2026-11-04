import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def build_url() -> str | URL:
    if explicit := os.getenv("DATABASE_URL"):
        return explicit
    user = os.getenv("ORACLE_USER")
    if user:
        return URL.create(
            "oracle+oracledb",
            username=user,
            password=os.getenv("ORACLE_PASSWORD", ""),
            host=os.getenv("ORACLE_HOST", "oracle.fiap.com.br"),
            port=int(os.getenv("ORACLE_PORT", "1521")),
            database=os.getenv("ORACLE_SID", "orcl"),  # vira SID no dialeto oracledb
        )
    # 3) Fallback local
    return "sqlite:///./clyvo_dev.db"


def make_engine(url: str | URL | None = None) -> Engine:
    return create_engine(url or build_url(), pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    """Dependência do FastAPI: uma sessão por requisição."""
    with SessionLocal() as session:
        yield session
