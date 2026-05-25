# scrapers/sunrise_scraper.py
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class SunriseScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://srm.com.tw/product.php?_path=product_showtimes"

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
                current_year = datetime.now().year

                idx = 0
                while idx < len(lines):
                    line = lines[idx]

                    if line in ["熱映中", "即將上映"]:
                        if idx + 1 < len(lines):
                            potential_title = lines[idx + 1]
                            if "請選擇" not in potential_title and "首頁" not in potential_title:
                                current_movie = potential_title
                                current_dates = []
                                current_format = "數位"
                        idx += 2
                        continue

                    if "星期" in line and idx + 2 < len(lines):
                        next_1 = lines[idx + 1]
                        next_2 = lines[idx + 2]
                        if next_1.isdigit() and "月" in next_2:
                            day = next_1.zfill(2)
                            month_match = re.search(r'\d+', next_2)
                            month = month_match.group(0).zfill(2) if month_match else "01"
                            current_dates.append(f"{current_year}-{month}-{day}")
                            idx += 3
                            continue

                    if "『" in line and "』" in line:
                        current_format = line.replace("『", "").replace("』", "")
                        idx += 1
                        continue

                    if re.match(r'^\d{2}:\d{2}$', line) and current_movie:
                        price = 340 if "3D" in current_format.upper() else 280
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
                                "format_type": current_format,
                                "language": "原文",
                                "price": price,
                                "seat_status": "現場售票"
                            })

                    idx += 1

            except Exception as e:
                print(f"[{theater_name}] 爬取失敗: {e}")
            finally:
                browser.close()

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")