# database.py
import os
from sqlmodel import create_engine, SQLModel, Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, 'movie_database.db')}"

engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

def init_db():
    from models import Theater, Showtime  # 延遲匯入，避免循環依賴
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session