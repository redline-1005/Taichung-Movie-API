# clean_db.py
from sqlmodel import Session, select
from database import engine
from models import Showtime

def clean_non_taichung_shinkong():
    print("🧹 開始執行資料庫外縣市新光影城清洗程序...")
    
    with Session(engine) as session:
        # 找出所有包含「新光影城」但名字裡「沒有台中」的場次
        statement = select(Showtime).where(
            Showtime.theater_name.contains("新光影城")
        )
        results = session.exec(statement).all()
        
        unwanted_count = 0
        for show in results:
            if "台中" not in show.theater_name:
                session.delete(show)
                unwanted_count += 1
                
        session.commit()
        print(f"✅ 清洗完畢！已成功從資料庫中永久刪除 {unwanted_count} 筆外縣市新光影城場次紀錄。")

if __name__ == "__main__":
    clean_non_taichung_shinkong()