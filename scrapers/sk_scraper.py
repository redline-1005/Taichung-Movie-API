# scrapers/sk_scraper.py
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class SKScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.skcinemas.com"
        self.taichung_cinema_id = "1003"  # 台中中港新光影城

    def fetch_theater_info(self): pass

    def fetch_showtimes(self, theater_name):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            captured_showtimes = {"content": None}

            def handle_response(response):
                if "GetSessionByCinemasIDForApp" in response.url and response.status == 200:
                    try:
                        captured_showtimes["content"] = response.json()
                    except Exception:
                        pass

            page.on("response", handle_response)
            try:
                # 直接前往台中中港頁面
                page.goto(
                    f"{self.base_url}/sessions?c={self.taichung_cinema_id}",
                    wait_until="networkidle",
                    timeout=60000
                )
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"[{theater_name}] 頁面載入失敗: {e}")
            finally:
                browser.close()

            self.parse_data(captured_showtimes["content"])

    def parse_data(self, raw_data):
        if not raw_data or not raw_data.get("result"):
            print("未取得有效資料")
            return

        data_obj = raw_data.get("data", {})
        films = data_obj.get("SessionFilm", [])
        movie_map = {f["FilmNameID"]: f.get("FilmName", "未知電影") for f in films if "FilmNameID" in f}

        sessions = data_obj.get("Session", [])
        print(f"[新光影城] 解析 {len(sessions)} 筆場次")

        for s in sessions:
            f_id = s.get("FilmNameID")
            movie_name = movie_map.get(f_id, "未知電影")
            f_type = s.get("FilmType") or "數位"

            raw_show_date = s.get("_showDate") or ""
            try:
                date_time = datetime.fromisoformat(raw_show_date[:16].replace("T", " "))
            except Exception:
                continue

            seats = s.get("SeatsAvailable")
            seat_status = f"剩餘 {seats} 個座位" if seats is not None else "尚有空位"

            if "MX4D" in f_type:
                price = 540
            elif "LUXE" in f_type:
                price = 370
            elif "3D" in f_type:
                price = 390
            else:
                price = 330

            self.showtime_results.append({
                "movie_name": movie_name,
                "theater_name": "台中中港新光影城",
                "date_time": date_time,
                "format_type": f_type,
                "language": "原文",
                "price": price,
                "seat_status": seat_status
            })