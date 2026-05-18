# showtime_scraper.py
import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class ShowtimeScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.showtimes.com.tw"
        
        # 🌟 密碼鎖精準對齊！站前店採雙 ID 融合技術，確保 S1+S2 完整呈現
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
            print(f"❌ 秀泰爬蟲錯誤：找不到 [{theater_name}] 對應的官方 ID。")
            return

        print(f"--- 正在啟動【金礦提煉引擎】完整解鎖秀泰影城 [{theater_name}] ---")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            bootstrap_payload = {"content": None}

            def handle_response(response):
                if "bootstrap" in response.url and response.status == 200:
                    try:
                        bootstrap_payload["content"] = response.json().get("payload", {})
                        print("🎯 成功捕獲秀泰全台場次大禮包 (Bootstrap)！")
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                # 拿清單中的第一個真實 ID 去引導網頁載入，藉此觸發大禮包
                target_url = f"{self.base_url}/info/cinema/{cinema_ids[0]}"
                page.goto(target_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"❌ 網頁載入出錯: {e}")
            finally:
                browser.close()

            if bootstrap_payload["content"]:
                # 🌟 核心升級：遍歷該影城對應的所有 ID（例如站前店會輪流跑 53 與 54）並將資料清洗入庫
                for cid in cinema_ids:
                    print(f"🔍 正在提煉分館 ID: [{cid}] 的場次數據...")
                    self.extract_showtimes_from_bootstrap(bootstrap_payload["content"], cid, theater_name)
            else:
                print("❌ 提煉失敗，未能成功攔截到 Bootstrap 封包。")

    def extract_showtimes_from_bootstrap(self, payload, cinema_id, theater_name):
        """全面解碼大禮包，將時區導正、格式切分、票價計算，並寫入結果"""
        # 1. 建立電影名稱字典對照表
        programs = payload.get("programs", [])
        movie_map = {p['id']: p['name'] for p in programs if 'id' in p and 'name' in p}
        
        # 2. 深入指定影城分館的 events 節點
        events_data = payload.get("eventsForCorporations", {})
        cinema_data = events_data.get(str(cinema_id)) or {}
        events_list = cinema_data.get("events", [])
        
        print(f"🎬 正在清洗並串接分館 [{cinema_id}] 的 {len(events_list)} 筆真實場次...")
        
        current_count = 0
        for event in events_list:
            p_id = event.get("programId")
            movie_name = movie_map.get(p_id, "未知電影")
            
            # 3. 處理國際時區轉換
            raw_start = event.get("startedAt") or ""
            date_time_str = "未知時間"
            if raw_start and "T" in raw_start:
                try:
                    clean_time_str = raw_start.replace("Z", "")
                    utc_time = datetime.fromisoformat(clean_time_str)
                    local_time = utc_time + timedelta(hours=8)
                    date_time_str = local_time.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_time_str = raw_start.replace("T", " ")[:16]

            # 4. 處理影廳規格與語言切分
            meta_obj = event.get("meta", {})
            format_raw = meta_obj.get("format") or "數位 英語"
            
            format_parts = format_raw.split()
            if len(format_parts) >= 2:
                f_type = format_parts[0]
                language = format_parts[1]
            else:
                f_type = format_raw
                language = "原文"

            # 5. 指派票價
            if "SCREENX" in f_type.upper(): price = 410
            elif "IMAX" in f_type.upper(): price = 380
            elif "3D" in f_type.upper(): price = 370
            else: price = 310

            # 6. 座位狀態
            status = event.get("status")
            seat_status = "開放購票" if status == "active" else "停止售票"

            # 7. 壓入最終快取
            self.showtime_results.append({
                "movie_name": movie_name,
                "theater_name": theater_name,
                "date_time": date_time_str,
                "format_type": f_type,
                "language": language,
                "price": price,
                "seat_status": seat_status
            })
            current_count += 1
            
        print(f"✅ 分館 [{cinema_id}] 清洗完畢，累計成功疊加 {current_count} 筆場次。")