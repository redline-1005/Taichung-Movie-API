# database.py
import os
from sqlmodel import create_engine, SQLModel, Session
from models import Theater, Showtime

# 1. 動態獲取當前 database.py 所在的資料夾絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. 確保檔名為 movie_database.db
sqlite_file_name = "movie_database.db"
sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, sqlite_file_name)}"

# connect_args 是為了防止 SQLite 在多執行緒（FastAPI）下塞車
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """初始化資料庫並建立表格"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """取得資料庫連線會話"""
    return Session(engine)