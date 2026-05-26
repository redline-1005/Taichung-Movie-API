# scrapers/vieshow_scraper.py
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

THEATER_VALUE_MAP = {
    "台中大遠百威秀影城": "15|TZ",
    "台中老虎城威秀影城": "3|TT01",
    "台中大魯閣新時代威秀影城": "31|MM",
}

class VieshowScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.vscinemas.com.tw"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        cinema_value = THEATER_VALUE_MAP.get(theater_name)
        if not cinema_value:
            print(f"[{theater_name}] 找不到對應的影城 value")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="zh-TW",
                timezone_id="Asia/Taipei",
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                # 先開啟網頁取得 session
                page.goto(f"{self.base_url}/vsweb/", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)

                page.screenshot(path="vieshow_debug.png")
                
                # 選取影城
                cinema_sel = page.locator("select[name='cinema']")
                if cinema_sel.count() == 0:
                    print(f"[{theater_name}] 找不到影城選單")
                    return

                cinema_sel.select_option(cinema_value)
                page.wait_for_timeout(3000)

                # 用 Playwright 內建的 fetch 呼叫 API（帶有瀏覽器 session）
                cascade_js = f"""
                async () => {{
                    const report = {{ success: false, data: [] }};
                    try {{
                        const mRes = await fetch(`/api/GetLstDicMovie?cinema={cinema_value}`);
                        if (!mRes.ok) {{
                            report.data.push({{ error: `GetLstDicMovie 失敗: ${{mRes.status}}` }});
                            return report;
                        }}
                        const movies = await mRes.json();
                        if (!movies || movies.length === 0) return report;

                        for (let m of movies) {{
                            const movieId = m.strValue;
                            const movieName = m.strText;
                            const dRes = await fetch(`/api/GetLstDicDate?cinema={cinema_value}&movie=${{movieId}}`);
                            if (!dRes.ok) continue;
                            const dates = await dRes.json();
                            if (!dates) continue;

                            for (let d of dates) {{
                                const showDate = d.strValue;
                                const sRes = await fetch(`/api/GetLstDicSession?cinema={cinema_value}&movie=${{movieId}}&date=${{showDate}}`);
                                if (!sRes.ok) continue;
                                const sessions = await sRes.json();
                                if (!sessions) continue;

                                for (let s of sessions) {{
                                    report.data.push({{
                                        raw_movie_name: movieName,
                                        show_date: showDate,
                                        session_text: s.strText
                                    }});
                                }}
                            }}
                        }}
                        report.success = true;
                    }} catch (err) {{
                        report.data.push({{ error: err.toString() }});
                    }}
                    return report;
                }}
                """

                result = page.evaluate(cascade_js)
                raw_results = result.get("data", [])

                for item in raw_results:
                    if "error" in item:
                        print(f"[{theater_name}] 錯誤: {item['error']}")
                        continue

                    raw_name = item.get("raw_movie_name", "")
                    show_date = item.get("show_date", "").replace("/", "-")
                    session_time = item.get("session_text", "")
                    if not session_time:
                        continue

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

                    try:
                        date_time = datetime.strptime(f"{show_date} {session_time}", "%Y-%m-%d %H:%M")
                    except Exception:
                        continue

                    f_upper = f_type.upper()
                    if "IMAX" in f_upper:
                        price = 440
                    elif "4DX" in f_upper:
                        price = 510
                    elif "3D" in f_upper:
                        price = 390
                    else:
                        price = 330

                    self.showtime_results.append({
                        "movie_name": movie_name,
                        "theater_name": theater_name,
                        "date_time": date_time,
                        "format_type": f_type,
                        "language": language,
                        "price": price,
                        "seat_status": "開放購票"
                    })

                print(f"[{theater_name}] 取得 {len(self.showtime_results)} 筆場次")

            except Exception as e:
                print(f"[{theater_name}] 爬取失敗: {e}")
            finally:
                browser.close()

        print(f"[{theater_name}] 完成，共 {len(self.showtime_results)} 筆")