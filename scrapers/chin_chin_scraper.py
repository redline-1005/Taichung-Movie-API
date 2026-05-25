# scrapers/chin_chin_scraper.py
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class ChinChinScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://www.ccmovie.com.tw/product.php?_path=product_showtimes"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)

                full_text = page.locator("body").inner_text() or ""
                lines = [l.strip() for l in full_text.split("\n") if l.strip()]

                current_movie = None
                current_dates = []
                current_format = "數位"
                current_language = "原文"
                current_year = datetime.now().year

                idx = 0
                while idx < len(lines):
                    line = lines[idx]

                    if line == "現正熱映":
                        if idx + 1 < len(lines):
                            potential_title = lines[idx + 1]
                            if "請選擇" not in potential_title and "首頁" not in potential_title:
                                current_movie = potential_title
                                current_dates = []
                                current_format = "數位"
                                current_language = "原文"
                        idx += 2
                        continue

                    if re.match(r'^\d{1,2}/\d{1,2}$', line) and idx + 1 < len(lines):
                        if "週" in lines[idx + 1]:
                            month, day = line.split("/")
                            current_dates.append(f"{current_year}-{month.zfill(2)}-{day.zfill(2)}")
                            idx += 2
                            continue

                    if "-" in line and any(fmt in line.upper() for fmt in ["2D", "3D", "IMAX", "ATMOS"]):
                        parts = line.split("-")
                        current_format = parts[0].strip()
                        if len(parts) > 1:
                            current_language = parts[1].strip()  # 修正：保留完整語言名稱
                        idx += 1
                        continue

                    if re.match(r'^\d{2}:\d{2}$', line) and current_movie:
                        price = 330 if "3D" in current_format.upper() else 270
                        dates_to_use = current_dates if current_dates else [datetime.now().strftime("%Y-%m-%d")]

                        for d_str in dates_to_use:
                            try:
                                date_time = datetime.strptime(f"{d_str} {line}", "%Y-%m-%d %H:%M")
                            except Exception:
                                continue
                            self.showtime_results.append({
                                "movie_name": current_movie,
                                "theater_name": theater_name,
                                "date_time": date_time,
                                "format_type": current_format.replace("2D", "數位"),
                                "language": current_language,
                                "price": price,
                                "seat_status": "現場售票"
                            })

                    idx += 1

            except Exception as e:
                print(f"[{theater_name}] 爬取失敗: {e}")
            finally:
                browser.close()

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")