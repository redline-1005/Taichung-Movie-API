# scrapers/vieshow_scraper.py
import re
import requests
from datetime import datetime
from .base_scraper import BaseMovieScraper

THEATER_VALUE_MAP = {
    "台中大遠百威秀影城": "15|TZ",
    "台中老虎城威秀影城": "3|TT01",
    "台中大魯閣新時代威秀影城": "31|MM",
}

API_BASE = "https://www.vscinemas.com.tw/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.vscinemas.com.tw/vsweb/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With": "XMLHttpRequest",
}

class VieshowScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        cinema_value = THEATER_VALUE_MAP.get(theater_name)
        if not cinema_value:
            print(f"[{theater_name}] 找不到對應的影城 value")
            return

        try:
            movies_res = requests.get(
                f"{API_BASE}/GetLstDicMovie",
                params={"cinema": cinema_value},
                headers=HEADERS,
                timeout=15
            )
            print(f"[{theater_name}] GetLstDicMovie 狀態碼: {movies_res.status_code}")
            movies = movies_res.json()
            if not movies:
                print(f"[{theater_name}] 未取得電影清單")
                return

            print(f"[{theater_name}] 取得 {len(movies)} 部電影")

            for m in movies:
                movie_id = m.get("strValue")
                raw_name = m.get("strText", "")

                match = re.match(r'^\((.*?)\)(.*)$', raw_name)
                if match:
                    meta_info = match.group(1)
                    movie_name = match.group(2).strip()
                else:
                    meta_info = "數位"
                    movie_name = raw_name

                meta_parts = meta_info.split()
                f_type = meta_parts[0] if meta_parts else "數位"
                language = meta_parts[1] if len(meta_parts) >= 2 else "原文"

                f_upper = f_type.upper()
                if "IMAX" in f_upper:
                    price = 440
                elif "4DX" in f_upper:
                    price = 510
                elif "3D" in f_upper:
                    price = 390
                else:
                    price = 330

                dates_res = requests.get(
                    f"{API_BASE}/GetLstDicDate",
                    params={"cinema": cinema_value, "movie": movie_id},
                    headers=HEADERS,
                    timeout=15
                )
                dates = dates_res.json()
                if not dates:
                    continue

                for d in dates:
                    show_date = d.get("strValue", "").replace("/", "-")

                    sessions_res = requests.get(
                        f"{API_BASE}/GetLstDicSession",
                        params={"cinema": cinema_value, "movie": movie_id, "date": show_date},
                        headers=HEADERS,
                        timeout=15
                    )
                    sessions = sessions_res.json()
                    if not sessions:
                        continue

                    for s in sessions:
                        session_time = s.get("strText", "")
                        if not session_time:
                            continue

                        try:
                            date_time = datetime.strptime(
                                f"{show_date} {session_time}", "%Y-%m-%d %H:%M"
                            )
                        except Exception:
                            continue

                        self.showtime_results.append({
                            "movie_name": movie_name,
                            "theater_name": theater_name,
                            "date_time": date_time,
                            "format_type": f_type,
                            "language": language,
                            "price": price,
                            "seat_status": "開放購票"
                        })

        except Exception as e:
            print(f"[{theater_name}] 爬取失敗: {e}")

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")