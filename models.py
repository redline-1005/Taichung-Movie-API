# models.py
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

# 影廳資訊模型
class Theater(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str # 影廳名稱
    branch: Optional[str] = None # 分店
    city: str # 所在地縣市
    district: str # 所在地行政區
    url: str # 官網網址

# 電影場次模型
class Showtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_name: str # 電影名稱
    theater_name: str # 影廳名稱
    date_time: str # 暫定為字串，方便儲存爬到的原始時間
    format_type: str # 播放方式 (數位, MX4D等)
    language: str # 語言 (原文, 中配)
    price: int # 原價價格
    seat_status: str # 座位空缺程度