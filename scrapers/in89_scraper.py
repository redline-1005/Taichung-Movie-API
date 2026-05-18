# in89_scraper.py
import re
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class In89Scraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://www.in89cinemax.com/"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        print(f"--- 🚀 in89【動態級聯表單·終極絕對定位引擎】啟動：[{theater_name}] ---")
        
        with sync_playwright() as p:
            # 開啟 headless=True 背景隱形加速狂飆
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                
                # 1. 觸發第一道機關：選擇影城喚醒隱藏選單
                initial_theater = page.locator("#dropTheater")
                if initial_theater.count() > 0:
                    initial_theater.select_option("15") # 15 = 台中豐原
                else:
                    page.locator("select[name='theater_item']").select_option("15")
                    
                print(" 👉 已觸發豐原店選項，等待伺服器生成專屬選單...")
                page.wait_for_timeout(2000) # 給予 2 秒讓後面的選單長出來
                
                # 2. 拿出 X 光照出的三把黃金鑰匙 (使用 Name 絕對定位)
                movie_sel = page.locator("select[name='movie_item']")
                date_sel = page.locator("select[name='movie_date']")
                session_sel = page.locator("select[name='field_item']")
                
                # 獲取所有電影選項
                movie_options = movie_sel.locator("option").all()
                movies = []
                for opt in movie_options:
                    val = opt.get_attribute("value")
                    txt = opt.inner_text().strip()
                    if val and "選擇" not in txt:
                        movies.append((val, txt))
                        
                print(f"🎬 成功奪取 {len(movies)} 部電影權限，開始高速雙層輪詢提取 (約需 20-30 秒)...")
                
                # 3. 啟動無情機器人遍歷
                for m_val, m_text in movies:
                    # 解析官方優美的格式: "穿著Prada的惡魔2-2D數位(英語)"
                    if "-" in m_text:
                        name_part = "-".join(m_text.split("-")[:-1]).strip()
                        meta_part = m_text.split("-")[-1].strip()
                        fmt = meta_part
                        lang = "原文"
                        if "(" in meta_part and ")" in meta_part:
                            fmt = meta_part.split("(")[0].strip()
                            lang = meta_part.split("(")[1].replace(")", "").strip()
                    else:
                        name_part = m_text.strip()
                        fmt = "數位"
                        lang = "原文"
                        
                    # 豐原 in89 基準票價對齊 (標準 320，3D/特殊廳疊加加價)
                    price = 320
                    if "3D" in fmt.upper(): price += 60
                    if any(k in fmt.upper() for k in ["LUXE", "COACH", "BOOM", "IMAX"]): price += 50
                    
                    # 模擬手指：切換電影
                    movie_sel.select_option(m_val)
                    page.wait_for_timeout(800) # 確保日期 API 載入完畢
                    
                    # 獲取該電影的所有排片日期
                    date_options = date_sel.locator("option").all()
                    dates = []
                    for opt in date_options:
                        val = opt.get_attribute("value")
                        txt = opt.inner_text().strip()
                        if val and "選擇" not in txt:
                            dates.append((val, txt))
                            
                    for d_val, d_text in dates:
                        date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', d_text)
                        if not date_match: continue
                        show_date = date_match.group(0).replace("/", "-")
                        
                        # 模擬手指：切換日期
                        date_sel.select_option(d_val)
                        page.wait_for_timeout(600) # 確保場次 API 載入完畢
                        
                        # 終極收割：獲取該日期的所有時間
                        session_options = session_sel.locator("option").all()
                        for s_opt in session_options:
                            s_text = s_opt.inner_text().strip()
                            time_match = re.search(r'\d{2}:\d{2}', s_text)
                            if time_match:
                                show_time = time_match.group(0)
                                self.showtime_results.append({
                                    "movie_name": name_part,
                                    "theater_name": theater_name,
                                    "date_time": f"{show_date} {show_time}",
                                    "format_type": fmt,
                                    "language": lang,
                                    "price": price,
                                    "seat_status": "開放購票"
                                })
                                
            except Exception as e:
                print(f"❌ in89 級聯引擎發生異常: {e}")
            finally:
                browser.close()
                
        print(f"✅ [{theater_name}] 完美收網，共計清洗出 {len(self.showtime_results)} 筆標準場次。")