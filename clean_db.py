# clean_db.py
from sqlmodel import Session, delete
from database import engine
from models import Showtime


def clean_non_taichung_shinkong():
    with Session(engine) as session:
        statement = delete(Showtime).where(
            Showtime.theater_name.contains("新光影城") &
            ~Showtime.theater_name.contains("台中")
        )
        result = session.exec(statement)
        session.commit()
    print(f"已刪除 {result.rowcount} 筆非台中新光影城場次")


if __name__ == "__main__":
    clean_non_taichung_shinkong()