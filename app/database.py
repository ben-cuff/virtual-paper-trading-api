import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

POSTGRES_DATABASE = os.getenv("POSTGRES_URL")

if not POSTGRES_DATABASE:
    raise ValueError("No POSTGRES_DATABASE environment variable set")

try:
    engine = create_engine(POSTGRES_DATABASE)
except Exception as e:
    raise RuntimeError(f"Failed to connect to the database: {str(e)}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
