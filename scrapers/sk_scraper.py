# sk_scraper.py
# scrapers/sk_scraper.py
# 新光影城台中中港店實作
import json
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class SKScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.skcinemas.com"

    def fetch_theater_info(self):
        print("--- 正在透過網頁監聽獲取影城清單 ---")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            captured_data = {"content": None}

            def handle_response(response):
                if "GetAllForApp" in response.url and response.status == 200:
                    try:
                        captured_data["content"] = response.json()
                        print("✅ 成功攔截到 API 回應！")
                    except Exception:
                        pass

            page.on("response", handle_response)
            try:
                page.goto(f"{self.base_url}/sessions", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"網頁載入出錯: {e}")
            finally:
                browser.close()

            response_json = captured_data["content"]
            
            if response_json and response_json.get('data'):
                cinemas = response_json.get('data', [])
                for cinema in cinemas:
                    c_name = cinema.get('CinemasName') or "未知影城"
                    c_id = cinema.get('CinemasID') or ""
                    
                    self.theater_results.append({
                        "name": c_name,
                        "branch": c_name,
                        "city": "台中市" if "台中" in str(c_name) else "其他城市",
                        "district": "待查",
                        "url": f"{self.base_url}/sessions?c={c_id}"
                    })
                print(f"成功整理出 {len(self.theater_results)} 間影城資訊")
            else:
                print("❌ 攔截成功但資料格式不符")

    def fetch_showtimes(self, cinema_id):
        print(f"--- 正在攔截影廳 [{cinema_id}] 的場次 ---")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            captured_showtimes = {"content": None}

            def handle_response(response):
                if "GetSessionByCinemasIDForApp" in response.url and response.status == 200:
                    try:
                        captured_showtimes["content"] = response.json()
                        print(f"✅ 成功攔截場次資料！")
                    except Exception:
                        pass

            page.on("response", handle_response)
            try:
                page.goto(f"{self.base_url}/sessions?c={cinema_id}", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"場次頁面載入失敗: {e}")
            finally:
                browser.close()

            self.parse_data(captured_showtimes["content"])

    def parse_data(self, raw_data):
        if not raw_data or not raw_data.get("result"):
            return
        
        data_obj = raw_data.get("data", {})
        
        # 1. 建立電影名稱 ID 對照表 (FilmNameID -> FilmName)
        films = data_obj.get("SessionFilm", [])
        movie_map = {}
        for f in films:
            f_id = f.get("FilmNameID")
            f_name = f.get("FilmName") or "未知電影"
            if f_id:
                movie_map[f_id] = f_name
                
        # 2. 遍歷 132 筆放映場次 (Session)
        sessions = data_obj.get("Session", [])
        print(f"🎬 正在解析並串接 {len(sessions)} 個放映場次的詳細細節...")
        
        for s in sessions:
            f_id = s.get("FilmNameID")
            movie_name = movie_map.get(f_id, "未知電影")
            f_type = s.get("FilmType") or "數位"
            
            # 3. 處理動態時間格式
            raw_show_date = s.get("_showDate") or ""
            date_time = raw_show_date.replace("T", " ")[:16] if raw_show_date else "未知時間"
            
            # 4. 處理動態座位狀況
            seats = s.get("SeatsAvailable")
            if seats is not None:
                seat_status = f"剩餘 {seats} 個座位"
            else:
                seat_status = "尚有空位"
                
            # 5. 修正處：對齊 2026 台中中港新光影城官方真實「全票」票價
            if "MX4D" in f_type:
                price = 540
            elif "LUXE" in f_type:
                price = 370
            elif "3D" in f_type:
                price = 390
            else:
                price = 330  # 包含數位版、日語版、國語版等標準 2D 廳
                
            # 存入結果快取
            self.showtime_results.append({
                "movie_name": movie_name,
                "theater_name": "新光影城",
                "date_time": date_time,
                "format_type": f_type,
                "language": "原文",
                "price": price,
                "seat_status": seat_status
            })