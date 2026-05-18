# database.py
from sqlmodel import create_engine, SQLModel, Session
from models import Theater, Showtime

sqlite_file_name = "movie_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def init_db():
    """初始化資料庫並建立表格"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """取得資料庫連線會話"""
    return Session(engine)