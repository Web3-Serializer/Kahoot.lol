import os
import time
import secrets
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/kahoot.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(8))
    token = Column(String, unique=True, index=True, default=lambda: secrets.token_urlsafe(32))
    username = Column(String, unique=True, index=True)
    credits = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(Float, default=lambda: time.time())


class GameSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: secrets.token_hex(8))
    user_id = Column(String, index=True)
    pin = Column(String)
    bot_count = Column(Integer, default=1)
    mode = Column(String, default="random")
    status = Column(String, default="idle")
    config = Column(Text, default="{}")
    created_at = Column(Float, default=lambda: time.time())


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
