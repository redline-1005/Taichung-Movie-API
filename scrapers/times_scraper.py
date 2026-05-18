# times_scraper.py
import re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class TimesScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.target_url = "https://www.timescinema.com.tw/times.php"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        print(f"--- 🚀 清水時代戲院【日期與分頁雙層自動導航引擎】啟動：[{theater_name}] ---")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                
                # 1. 抓取首頁最上方的「日期頁籤」
                initial_text = page.locator("body").inner_text() or ""
                initial_lines = [l.strip() for l in initial_text.split("\n") if l.strip()]
                
                date_tabs = []
                for line in initial_lines[:20]:
                    if re.search(r'\d+月\d+日', line):
                        date_tabs.append(line)
                        
                print(f"🗓️ 掃描到 {len(date_tabs)} 個日期區間: {date_tabs}")
                if not date_tabs:
                    date_tabs = ["5月17日"] # 防呆
                
                current_year = 2026
                
                # 2. 第一層迴圈：遍歷每一個日期頁籤
                for tab_text in date_tabs:
                    print(f"\n 👉 準備進入日期頁籤: [{tab_text}]")
                    try:
                        tab_btn = page.locator(f"text='{tab_text}'").first
                        if tab_btn.count() > 0:
                            tab_btn.click(timeout=3000)
                            page.wait_for_timeout(1500)
                    except Exception:
                        pass
                        
                    # 拆解日期字串 (將 "5月16日~5月17日" 擴充成兩天的 YYYY-MM-DD 格式)
                    target_dates = []
                    matches = re.findall(r'(\d+)月(\d+)日', tab_text)
                    if len(matches) == 2:
                        m1, d1 = int(matches[0][0]), int(matches[0][1])
                        m2, d2 = int(matches[1][0]), int(matches[1][1])
                        try:
                            start_date = date(current_year, m1, d1)
                            end_date = date(current_year, m2, d2)
                            if end_date < start_date: end_date = date(current_year + 1, m2, d2)
                            delta_days = (end_date - start_date).days
                            for i in range(delta_days + 1):
                                target_dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
                        except Exception:
                            target_dates.append(f"{current_year}-{m1:02d}-{d1:02d}")
                    elif len(matches) == 1:
                        target_dates.append(f"{current_year}-{int(matches[0][0]):02d}-{int(matches[0][1]):02d}")
                    else:
                        target_dates.append(f"{current_year}-05-17")
                    
                    # 3. 第二層迴圈：處理該日期下的「多個分頁」 (1, 2, 3...)
                    current_page_num = 1
                    while True:
                        print(f"   📄 正在抽取第 {current_page_num} 頁資料...")
                        
                        current_text = page.locator("body").inner_text() or ""
                        lines = [l.strip() for l in current_text.split("\n") if l.strip()]
                        
                        current_movie = None
                        current_format = "數位"
                        current_language = "原文"
                        
                        # 解析目前畫面的純文字時刻表
                        for line in lines:
                            # 強化過濾器：把分頁標籤的 NEXT、PREV 也濾掉
                            if any(line.startswith(kw) for kw in ["回首頁", "廳別", "片長", "上映日期", "導演", "演員", "網頁設計", "TEL:", "FAX:", "PREV", "NEXT", "<", ">"]) or line.isdigit() or line == "":
                                continue
                                
                            if re.search(r'\d+月\d+日', line): continue
                                
                            times = re.findall(r'\b\d{2}:\d{2}\b', line)
                            if times:
                                if current_movie:
                                    for t in times:
                                        for d_str in target_dates: # 把時間分發給這個區間的每一天
                                            self.showtime_results.append({
                                                "movie_name": current_movie,
                                                "theater_name": theater_name,
                                                "date_time": f"{d_str} {t}",
                                                "format_type": current_format,
                                                "language": current_language,
                                                "price": 270,
                                                "seat_status": "現場售票"
                                            })
                                continue
                                
                            raw_title = line
                            fmt = "數位"
                            lang = "原文"
                            if "中文" in raw_title or "國語" in raw_title: lang = "國語"
                            if "3D" in raw_title.upper(): fmt = "3D"
                            clean_title = re.sub(r'\(數位版\)|\(3D版\)|\(中文版\)|\(國語版\)|中文版|國語版', '', raw_title).strip()
                            
                            if clean_title:
                                current_movie = clean_title
                                current_format = fmt
                                current_language = lang
                                
                        # 4. 尋找下一頁的按鈕 (例如尋找文字剛好是 "2"、"3" 的超連結)
                        current_page_num += 1
                        # 使用精準匹配，尋找 <a> 標籤且文字完全等於下一頁數字的元素
                        next_page_btn = page.locator(f"a:text-is('{current_page_num}')").first
                        
                        if next_page_btn.count() > 0:
                            print(f"   👉 發現第 {current_page_num} 頁！自動翻頁中...")
                            next_page_btn.click()
                            page.wait_for_timeout(1500) # 等待新頁面載入
                        else:
                            print(f"   🛑 第 {current_page_num-1} 頁已是該區間最後一頁，換下一個日期。")
                            break # 跳出分頁迴圈，繼續下一個日期頁籤
                            
            except Exception as e:
                print(f"❌ 時代戲院解碼引擎發生異常: {e}")
            finally:
                browser.close()
                
        print(f"✅ [{theater_name}] 完美收網，共計清洗出 {len(self.showtime_results)} 筆標準場次。")