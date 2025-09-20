# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# # Create engine with SSL
# engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Prevents stale connection errors
    pool_size=20,            # Number of persistent connections per worker
    max_overflow=20,         # Allow bursts (up to 40 connections per worker)
    pool_timeout=30,         # Wait 30s if pool is full before erroring
    pool_recycle=1800,       # Recycle every 30 minutes to avoid idle timeouts
    # connect_args={"sslmode": "require"},  # Uncomment if Neon requires
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
