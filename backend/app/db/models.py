from sqlalchemy import MetaData, Table, Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("email", String, unique=True, index=True),
    Column("password_hash", String),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("price", Float),
    Column("stock", Integer),
    Column("image", String),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, index=True, nullable=True),
    Column("items", JSON),
    Column("total", Float),
    Column("status", String),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

chat_messages = Table(
    "chat_messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("thread_id", String, index=True),
    Column("message", String),
    Column("role", String),
    Column("read", Boolean, default=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)
