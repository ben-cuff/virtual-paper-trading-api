import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

URL_DATABASE = os.getenv("POSTGRES_URL")

if not URL_DATABASE:
    raise ValueError("No DATABASE_URL environment variable set")

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
