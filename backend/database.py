import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Check if PostgreSQL driver is installed
has_postgres_driver = False
try:
    import psycopg2
    has_postgres_driver = True
except ImportError:
    pass

# Robust fallback to SQLite if DATABASE_URL is not set, driver is missing, or connection fails
if not DATABASE_URL or (DATABASE_URL.startswith("postgresql") and not has_postgres_driver):
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        print("⚠️ psycopg2 driver is not installed. Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///./notices.db"

try:
    if DATABASE_URL.startswith("postgresql"):
        # Create engine and verify connection
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
except Exception as e:
    print(f"⚠️ Database connection failed ({e}). Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///./notices.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
