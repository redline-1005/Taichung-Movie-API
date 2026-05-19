# main_api.py
from typing import List, Optional
from fastapi import FastAPI, Depends, Query
from sqlmodel import Session, select
from database import engine, get_session 
from models import Showtime, Theater 

app = FastAPI(
    title="台中電影院時刻表整合 API",
    description="RedLine通識課作業，可以快速找到台中電影場次，已完美對齊雲端全自動化生產線。",
    version="1.2.0"
)

@app.get("/")
def root():
    return {"status": "online", "message": "歡迎使用大台中影城時刻表 API，請至 /docs 檢視文件。"}

# 核心端點 1：查詢所有場次
@app.get("/api/showtimes", response_model=List[Showtime])
def get_showtimes(
    movie_name: Optional[str] = Query(None, description="電影名稱關鍵字"),
    theater_name: Optional[str] = Query(None, description="特定影城名稱"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)  # 🌟 統一使用 database.py 的會話供應器
):
    statement = select(Showtime)
    
    # 🌟 核心防禦：如果影城名包含新光影城，但排除掉不含「台中」的場次 (防外縣市間諜)
    statement = statement.where(
        ~((Showtime.theater_name.contains("新光影城")) & (~Showtime.theater_name.contains("台中")))
    )
    
    if movie_name:
        statement = statement.where(Showtime.movie_name.contains(movie_name))
    if theater_name:
        statement = statement.where(Showtime.theater_name.contains(theater_name))
        
    statement = statement.order_by(Showtime.date_time).offset(offset).limit(limit)
    results = session.exec(statement).all()
    return results

# 輔助端點 2：獲取目前上映中的不重複電影清單
@app.get("/api/movies", response_model=List[str])
def get_active_movies(session: Session = Depends(get_session)):
    all_showtimes = session.exec(select(Showtime)).all()
    
    clean_showtimes = [
        s for s in all_showtimes 
        if not ("新光影城" in s.theater_name and "台中" not in s.theater_name)
    ]
    return list(set([s.movie_name for s in clean_showtimes]))

# 輔助端點 3：獲取系統中的影城清單（改為直接讀取 Theater 資料表，完美回傳 11 間核心分店）
@app.get("/api/theaters", response_model=List[Theater])
def get_active_theaters(session: Session = Depends(get_session)):
    # 🌟 直接去 Theater 資料表把我們初始化的 11 間台中黃金名冊撈出來！
    theaters = session.exec(select(Theater)).all()
    return theaters