# models.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class Theater(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    branch: Optional[str] = None
    city: str
    district: str
    url: str


class Showtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_name: str
    theater_name: str
    date_time: datetime
    format_type: str
    language: str
    price: Optional[int] = None
    seat_status: Optional[str] = None