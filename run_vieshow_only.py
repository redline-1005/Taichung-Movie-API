# run_vieshow_only.py
import re
from sqlmodel import Session, delete
from sqlalchemy import and_
from database import engine
from models import Showtime
from scrapers.vieshow_scraper import VieshowScraper

VIESHOW_THEATERS = [
    "台中大遠百威秀影城",
    "台中老虎城威秀影城",
    "台中大魯閣新時代威秀影城",
]

def normalize_movie_name(name: str) -> str:
    import re
    name = name.replace("：", ":").replace("∶", ":")
    name = re.sub(r'\s*:\s*', ": ", name)
    name = name.replace("_", " ")
    name = re.sub(r'\s*-([^-]+)-\s*', r' \1', name)
    name = name.replace("Ⅱ", "II").replace("Ⅰ", "I").replace("Ⅲ", "III")
    name = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', name)
    name = re.sub(r'([\u4e00-\u9fff])([A-Za-z])', r'\1 \2', name)
    name = re.sub(r'(\d)([\u4e00-\u9fff])', r'\1 \2', name)
    name = re.sub(r'([A-Za-z])([\u4e00-\u9fff])', r'\1 \2', name)
    name = re.sub(r'([\u4e00-\u9fff\u3040-\u30ff])\s+([\u4e00-\u9fff\u3040-\u30ff！。，、？：；「」『』【】〔〕…—])', r'\1\2', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def update_vieshow_only():
    print("開始更新威秀場次資料")

    with Session(engine) as session:
        # 只刪除威秀的舊資料
        for theater_name in VIESHOW_THEATERS:
            session.exec(
                delete(Showtime).where(Showtime.theater_name == theater_name)
            )
        session.commit()
        print("威秀舊資料清除完畢")

        for theater_name in VIESHOW_THEATERS:
            print(f"處理中: {theater_name}")
            try:
                scraper = VieshowScraper()
                scraper.fetch_showtimes(theater_name)

                for s_data in scraper.showtime_results:
                    s_data["theater_name"] = theater_name
                    s_data["movie_name"] = normalize_movie_name(s_data["movie_name"])
                    session.add(Showtime(**s_data))

                session.commit()
                print(f"完成: {theater_name}，共 {len(scraper.showtime_results)} 筆")

            except Exception as e:
                print(f"失敗: {theater_name}，原因: {e}")
                session.rollback()

    print("威秀更新完畢")

if __name__ == "__main__":
    update_vieshow_only()