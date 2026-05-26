# main_scraper.py
import re
from sqlmodel import Session, delete
from database import engine
from models import Showtime

from scrapers.in89_scraper import In89Scraper
from scrapers.times_scraper import TimesScraper
from scrapers.sk_scraper import SKScraper
from scrapers.vieshow_scraper import VieshowScraper
from scrapers.showtime_scraper import ShowtimeScraper
from scrapers.chin_chin_scraper import ChinChinScraper
from scrapers.sunrise_scraper import SunriseScraper

THEATER_SCRAPER_MAP = [
    ("豐原in89豪華影城",        In89Scraper),
    ("清水時代戲院",             TimesScraper),
    ("親親大戲院",               ChinChinScraper),
    ("日日新大戲院",             SunriseScraper),
    ("台中中港新光影城",         SKScraper),
    ("台中大遠百威秀影城",       VieshowScraper),
    ("台中老虎城威秀影城",       VieshowScraper),
    ("台中大魯閣新時代威秀影城", VieshowScraper),
    ("台中站前秀泰影城",         ShowtimeScraper),
    ("台中文心秀泰影城",         ShowtimeScraper),
    ("台中麗寶秀泰影城",         ShowtimeScraper),
]


def normalize_movie_name(name: str) -> str:
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


def update_all_taichung_showtimes():
    print("開始更新台中場次資料")

    with Session(engine) as session:
        session.exec(delete(Showtime))
        session.commit()
        print("舊資料清除完畢")

        for theater_name, ScraperClass in THEATER_SCRAPER_MAP:
            print(f"處理中: {theater_name}")
            try:
                scraper = ScraperClass()
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

    print("所有影城更新完畢")


if __name__ == "__main__":
    update_all_taichung_showtimes()