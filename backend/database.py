import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Fallback to a local SQLite database for local dev if Postgres isn't running yet.
# When in production, this should be: postgresql://user:password@localhost/tridentwear db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tridentwear.db")

# SQLite needs check_same_thread=False for FastAPI. Postgres does not.
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
