from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_hub.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Retry logic for DB connection
import time
from sqlalchemy.exc import OperationalError

def wait_for_db():
    retries = 30
    while retries > 0:
        try:
            # Try to connect
            with engine.connect() as connection:
                print("Database connected!")
                return
        except OperationalError:
            print(f"Database not ready, retrying in 2 seconds... ({retries} left)")
            time.sleep(2)
            retries -= 1
    print("Could not connect to database after retries.")

wait_for_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
