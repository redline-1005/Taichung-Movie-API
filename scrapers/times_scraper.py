# scrapers/times_scraper.py
import re
from datetime import date, datetime, timedelta
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

SKIP_PREFIXES = ["回首頁", "廳別", "片長", "上映日期", "導演", "演員", "網頁設計", "TEL:", "FAX:", "PREV", "NEXT", "輔導級", "普遍級", "限制級", "保護級"]

class TimesScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://www.timescinema.com.tw/times.php"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)

                initial_text = page.locator("body").inner_text() or ""
                initial_lines = [l.strip() for l in initial_text.split("\n") if l.strip()]

                date_tabs = [l for l in initial_lines[:20] if re.search(r'\d+月\d+日', l)]
                if not date_tabs:
                    date_tabs = [datetime.now().strftime("%-m月%-d日")]

                current_year = datetime.now().year

                for tab_text in date_tabs:
                    try:
                        tab_btn = page.locator(f"text='{tab_text}'").first
                        if tab_btn.count() > 0:
                            tab_btn.click(timeout=3000)
                            page.wait_for_timeout(1500)
                    except Exception:
                        pass

                    target_dates = self._parse_date_range(tab_text, current_year)

                    current_page_num = 1
                    while True:
                        current_text = page.locator("body").inner_text() or ""
                        lines = [l.strip() for l in current_text.split("\n") if l.strip()]

                        current_movie = None
                        current_format = "數位"
                        current_language = "原文"

                        for line in lines:
                            if any(line.startswith(kw) for kw in SKIP_PREFIXES) or line.isdigit():
                                continue
                            if re.search(r'\d+月\d+日', line):
                                continue

                            times = re.findall(r'\b\d{2}:\d{2}\b', line)
                            if times:
                                if current_movie:
                                    # 修正票價：2D 230元，3D 280元
                                    price = 280 if "3D" in current_format.upper() else 230
                                    for t in times:
                                        for d_str in target_dates:
                                            try:
                                                date_time = datetime.strptime(f"{d_str} {t}", "%Y-%m-%d %H:%M")
                                            except Exception:
                                                continue
                                            self.showtime_results.append({
                                                "movie_name": current_movie,
                                                "theater_name": theater_name,
                                                "date_time": date_time,
                                                "format_type": current_format,
                                                "language": current_language,
                                                "price": price,
                                                "seat_status": "現場售票"
                                            })
                                continue

                            raw_title = line
                            fmt = "3D" if "3D" in raw_title.upper() else "數位"
                            lang = "國語" if ("中文" in raw_title or "國語" in raw_title) else "原文"
                            clean_title = re.sub(r'\(數位版\)|\(3D版\)|\(中文版\)|\(國語版\)|中文版|國語版|\(數位\)|\(3D\)', '', raw_title).strip()
                            if clean_title:
                                current_movie = clean_title
                                current_format = fmt
                                current_language = lang

                        current_page_num += 1
                        next_btn = page.locator(f"a:text-is('{current_page_num}')").first
                        if next_btn.count() > 0:
                            next_btn.click()
                            page.wait_for_timeout(1500)
                        else:
                            break

            except Exception as e:
                print(f"[{theater_name}] 爬取失敗: {e}")
            finally:
                browser.close()

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")

    def _parse_date_range(self, tab_text, current_year):
        matches = re.findall(r'(\d+)月(\d+)日', tab_text)
        if len(matches) == 2:
            try:
                m1, d1 = int(matches[0][0]), int(matches[0][1])
                m2, d2 = int(matches[1][0]), int(matches[1][1])
                start = date(current_year, m1, d1)
                end = date(current_year, m2, d2)
                if end < start:
                    end = date(current_year + 1, m2, d2)
                return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]
            except Exception:
                pass
        if len(matches) == 1:
            return [f"{current_year}-{int(matches[0][0]):02d}-{int(matches[0][1]):02d}"]
        return [datetime.now().strftime("%Y-%m-%d")]