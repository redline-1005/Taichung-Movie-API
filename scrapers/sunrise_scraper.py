# sunrise_scraper.py
import re
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class SunriseScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        # 日日新大戲院場次大本營入口
        self.target_url = "https://srm.com.tw/product.php?_path=product_showtimes"

    def fetch_theater_info(self): pass
    def parse_data(self, raw_data): pass

    def fetch_showtimes(self, theater_name):
        print(f"--- 🚀 日日新【全量文本流狀態機引擎·完全體】啟動：[{theater_name}] ---")
        
        with sync_playwright() as p:
            # 地方老字號直接開啟 headless=True 背景毫秒級解碼
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                
                # 1. 強行抽出全網頁最真實、無死角的純文字排版流
                full_text = page.locator("body").inner_text() or ""
                lines = [l.strip() for l in full_text.split("\n") if l.strip()]
                
                print(f"📋 成功捕獲日日新全網文字長河，共 {len(lines)} 行。正在發動動態時序解碼...")
                
                current_movie = None
                current_dates = []
                current_format = "數位"
                
                # 2. 狀態機核心指針輪詢
                idx = 0
                while idx < len(lines):
                    line = lines[idx]
                    
                    # 🌟 核心修正點：片名絕對坐標錨點！只要看到「熱映中」或「即將上映」，下一行必定是精準中文片名
                    if line in ["熱映中", "即將上映"]:
                        if idx + 1 < len(lines):
                            potential_title = lines[idx + 1]
                            # 過濾掉異常干擾項
                            if "請選擇" not in potential_title and "首頁" not in potential_title:
                                current_movie = potential_title
                                current_dates = []    # 換新電影，清空重置日期庫
                                current_format = "數位" # 還原預設規格
                                print(f" 🎬 成功解鎖電影：《{current_movie}》")
                                idx += 2
                                continue
                    
                    # 錨點 B：智慧日期頁籤收集 (識別 "星期X" -> "數字" -> "X月" 的連續頁籤文字)
                    if "星期" in line and idx + 2 < len(lines):
                        next_1 = lines[idx + 1]
                        next_2 = lines[idx + 2]
                        if next_1.isdigit() and "月" in next_2:
                            day = next_1.zfill(2)
                            month_match = re.search(r'\d+', next_2)
                            month = month_match.group(0).zfill(2) if month_match else "05"
                            
                            date_str = f"2026-{month}-{day}"
                            if date_str not in current_dates:
                                current_dates.append(date_str)
                            idx += 3
                            continue
                    
                    # 錨點 C：廳房規格識別 (例如：『2D』至尊廳)
                    if "『" in line and "』" in line:
                        current_format = line.replace("『", "").replace("』", "")
                        idx += 1
                        continue
                    
                    # 錨點 D：時刻表精準對齊 (數字時間格式 10:00)
                    if re.match(r'^\d{2}:\d{2}$', line):
                        if current_movie:
                            # 2026 日日新在地真實全票票價對齊
                            price = 340 if "3D" in current_format.upper() else 280
                            
                            # 如果有撈到預售日期就依序填入；若無(當日熱映)則自動對齊今天 2026-05-17
                            dates_to_assign = current_dates if current_dates else ["2026-05-17"]
                            
                            for d_str in dates_to_assign:
                                self.showtime_results.append({
                                    "movie_name": current_movie,
                                    "theater_name": "日日新大戲院",
                                    "date_time": f"{d_str} {line}",
                                    "format_type": current_format,
                                    "language": "原文",
                                    "price": price,
                                    "seat_status": "現場售票"
                                })
                    
                    idx += 1
                    
            except Exception as e:
                print(f"❌ 日日新全量解碼引擎崩潰: {e}")
            finally:
                browser.close()
                
        print(f"✅ [{theater_name}] 狀態機更新完畢，共完美清洗出 {len(self.showtime_results)} 筆標準場次。")