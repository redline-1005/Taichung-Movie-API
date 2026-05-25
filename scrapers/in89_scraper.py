# scrapers/in89_scraper.py
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class In89Scraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://www.in89cinemax.com/"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)

                try:
                    page.wait_for_selector("#dropTheater", timeout=10000)
                except Exception:
                    print(f"[{theater_name}] 找不到影城選單")
                    return

                theater_sel = page.locator("#dropTheater")
                theater_sel.select_option("15")
                page.wait_for_timeout(2500)

                movie_sel = page.locator("select[name='movie_item']")
                date_sel = page.locator("select[name='movie_date']")
                session_sel = page.locator("select[name='field_item']")

                movies = [
                    (opt.get_attribute("value"), opt.inner_text().strip())
                    for opt in movie_sel.locator("option").all()
                    if opt.get_attribute("value") and "選擇" not in opt.inner_text()
                ]

                print(f"[{theater_name}] 取得 {len(movies)} 部電影")

                for m_val, m_text in movies:
                    if "-" in m_text:
                        name_part = "-".join(m_text.split("-")[:-1]).strip()
                        meta_part = m_text.split("-")[-1].strip()
                        if "(" in meta_part and ")" in meta_part:
                            fmt = meta_part.split("(")[0].strip()
                            lang = meta_part.split("(")[1].replace(")", "").strip()
                        else:
                            fmt = meta_part
                            lang = "原文"
                    else:
                        name_part = m_text.strip()
                        fmt = "數位"
                        lang = "原文"

                    price = 320
                    if "3D" in fmt.upper():
                        price += 60
                    if any(k in fmt.upper() for k in ["LUXE", "COACH", "BOOM", "IMAX"]):
                        price += 50

                    movie_sel.select_option(m_val)
                    page.wait_for_timeout(800)

                    dates = [
                        (opt.get_attribute("value"), opt.inner_text().strip())
                        for opt in date_sel.locator("option").all()
                        if opt.get_attribute("value") and "選擇" not in opt.inner_text()
                    ]

                    for d_val, d_text in dates:
                        date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', d_text)
                        if not date_match:
                            continue
                        show_date = date_match.group(0).replace("/", "-")

                        date_sel.select_option(d_val)
                        page.wait_for_timeout(600)

                        for s_opt in session_sel.locator("option").all():
                            s_text = s_opt.inner_text().strip()
                            time_match = re.search(r'\d{2}:\d{2}', s_text)
                            if time_match:
                                try:
                                    date_time = datetime.strptime(
                                        f"{show_date} {time_match.group(0)}", "%Y-%m-%d %H:%M"
                                    )
                                except Exception:
                                    continue
                                self.showtime_results.append({
                                    "movie_name": name_part,
                                    "theater_name": theater_name,
                                    "date_time": date_time,
                                    "format_type": fmt,
                                    "language": lang,
                                    "price": price,
                                    "seat_status": "開放購票"
                                })

            except Exception as e:
                print(f"[{theater_name}] 爬取失敗: {e}")
            finally:
                browser.close()

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")