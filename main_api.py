# main_api.py
from typing import List, Optional
from fastapi import FastAPI, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import distinct
from database import get_session
from models import Showtime, Theater

app = FastAPI(
    title="台中電影院時刻表整合 API",
    version="1.0.0"
)

def is_taichung_theater(statement):
    """排除非台中的新光影城場次"""
    return statement.where(
        ~((Showtime.theater_name.contains("新光影城")) & 
          (~Showtime.theater_name.contains("台中")))
    )

@app.get("/")
def root():
    return {"status": "online", "message": "請至 /docs 檢視 API 文件"}

@app.get("/api/showtimes", response_model=List[Showtime])
def get_showtimes(
    movie_name: Optional[str] = Query(None, description="電影名稱關鍵字"),
    theater_name: Optional[str] = Query(None, description="影城名稱關鍵字"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)
):
    statement = is_taichung_theater(select(Showtime))

    if movie_name:
        statement = statement.where(Showtime.movie_name.contains(movie_name))
    if theater_name:
        statement = statement.where(Showtime.theater_name.contains(theater_name))

    statement = statement.order_by(Showtime.date_time).offset(offset).limit(limit)
    return session.exec(statement).all()

@app.get("/api/movies", response_model=List[str])
def get_active_movies(session: Session = Depends(get_session)):
    statement = is_taichung_theater(
        select(distinct(Showtime.movie_name))
    )
    return session.exec(statement).all()

@app.get("/api/theaters", response_model=List[Theater])
def get_active_theaters(session: Session = Depends(get_session)):
    return session.exec(select(Theater)).all()