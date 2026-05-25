# scrapers/showtime_scraper.py
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class ShowtimeScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.showtimes.com.tw"
        self.theater_id_map = {
            "台中站前秀泰影城": ["53", "54"],
            "台中文心秀泰影城": ["58"],
            "台中麗寶秀泰影城": ["60"]
        }

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        cinema_ids = self.theater_id_map.get(theater_name)
        if not cinema_ids:
            print(f"找不到 [{theater_name}] 對應的 ID")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            bootstrap_payload = {"content": None}

            def handle_response(response):
                if "bootstrap" in response.url and response.status == 200:
                    try:
                        bootstrap_payload["content"] = response.json().get("payload", {})
                    except Exception:
                        pass

            page.on("response", handle_response)
            try:
                page.goto(f"{self.base_url}/info/cinema/{cinema_ids[0]}", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"頁面載入失敗: {e}")
            finally:
                browser.close()

            if bootstrap_payload["content"]:
                for cid in cinema_ids:
                    self._extract_showtimes(bootstrap_payload["content"], cid, theater_name)
            else:
                print(f"[{theater_name}] 未能攔截到場次資料")

    def _extract_showtimes(self, payload, cinema_id, theater_name):
        programs = payload.get("programs", [])
        movie_map = {p["id"]: p["name"] for p in programs if "id" in p and "name" in p}

        events_data = payload.get("eventsForCorporations", {})
        cinema_data = events_data.get(str(cinema_id)) or {}
        events_list = cinema_data.get("events", [])

        for event in events_list:
            p_id = event.get("programId")
            movie_name = movie_map.get(p_id, "未知電影")

            raw_start = event.get("startedAt") or ""
            try:
                utc_time = datetime.fromisoformat(raw_start.replace("Z", ""))
                date_time = utc_time + timedelta(hours=8)
            except Exception:
                continue

            meta_obj = event.get("meta", {})
            format_raw = meta_obj.get("format") or "數位 原文"
            format_parts = format_raw.split()
            f_type = format_parts[0] if format_parts else "數位"
            language = format_parts[1] if len(format_parts) >= 2 else "原文"

            f_upper = f_type.upper()
            if "SCREENX" in f_upper:
                price = 410
            elif "IMAX" in f_upper:
                price = 380
            elif "3D" in f_upper:
                price = 370
            else:
                price = 310

            status = event.get("status")
            seat_status = "開放購票" if status == "active" else "停止售票"

            self.showtime_results.append({
                "movie_name": movie_name,
                "theater_name": theater_name,
                "date_time": date_time,
                "format_type": f_type,
                "language": language,
                "price": price,
                "seat_status": seat_status
            })