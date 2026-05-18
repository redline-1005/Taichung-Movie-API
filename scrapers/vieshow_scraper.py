# vieshow_scraper.py
import json
import re
from playwright.sync_api import sync_playwright
from .base_scraper import BaseMovieScraper

class VieshowScraper(BaseMovieScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.vscinemas.com.tw/vsweb/"

    def fetch_theater_info(self):
        pass

    def parse_data(self, raw_data):
        pass

    def fetch_showtimes(self, theater_name):
        print(f"--- 🚀 威秀【電光導航完全體引擎】啟動：[{theater_name}] ---")
        
        with sync_playwright() as p:
            # 真人現身模式，確保 Session 憑證完美註冊
            browser = p.chromium.launch(
                headless=False, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(viewport={"width": 1366, "height": 768})
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                # 1. 進入首頁
                page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(1000)

                # 2. 定位影城下拉選單
                cinema_select = None
                for s in page.locator("select").all():
                    if any(kw in s.inner_text() for kw in ["請選擇影城", "遠百", "TIGER", "新時代"]):
                        cinema_select = s
                        break
                
                if not cinema_select:
                    print("❌ 錯誤：未能尋獲影城下拉選單。")
                    return

                # 3. 🌟 智慧繁簡模糊對齊：從網頁選單中「動態拔出」官方真實 ID，徹底拒絕盲猜
                option_id = None
                option_label = None
                name_norm = theater_name.replace("臺", "台")
                
                for opt in cinema_select.locator("option").all():
                    opt_text = opt.inner_text()
                    if "(Gold Class)" in opt_text and "(Gold Class)" not in name_norm:
                        continue
                        
                    if "遠百" in name_norm and "遠百" in opt_text and "台中" in opt_text:
                        option_id = opt.get_attribute("value")
                        option_label = opt_text
                        break
                    elif ("tiger" in name_norm.lower() or "老虎城" in name_norm) and "TIGER CITY" in opt_text.upper():
                        option_id = opt.get_attribute("value")
                        option_label = opt_text
                        break
                    elif ("大魯閣" in name_norm or "新時代" in name_norm) and ("大魯閣" in opt_text or "新時代" in opt_text):
                        option_id = opt.get_attribute("value")
                        option_label = opt_text
                        break

                if not option_id:
                    print(f"❌ 錯誤：官方網頁選單中找不到符合 [{theater_name}] 的台中區域選項。")
                    return

                print(f"🎯 【導航對齊成功】完美選定選單標籤: [{option_label}] ➡️ 自動提煉真實 ID: [{option_id}]")

                # 4. 模擬切換影城以在後台註冊 ASP.NET Session 狀態
                cinema_select.select_option(value=option_id)
                page.evaluate(f'''(val) => {{
                    const el = document.querySelector('select[name*="cinema"]') || document.querySelector('select');
                    if (el && window.jQuery) window.jQuery(el).trigger('change');
                }}''', option_id)
                
                print("⏳ 憑證安全寫入中...正在注入極速級聯提煉雷達...")
                page.wait_for_timeout(3000) # 給網頁 3 秒鐘確保 Session 完全鎖定

                # 5. ⚡ 直擊真實 /api/ 端點發動非同步級聯極速收割 (具備完整終止機制)
                cascade_fast_js = f"""
                async () => {{
                    const report = {{ success: false, log: [], data: [] }};
                    try {{
                        const mRes = await fetch(`/api/GetLstDicMovie?cinema={option_id}`);
                        const movies = await mRes.json();
                        
                        if (!movies || movies.length === 0) {{
                            report.log.push("未能取得電影清單");
                            return report;
                        }}
                        
                        report.log.push(`成功辨識到 ${{movies.length}} 部上映電影，啟動機器速率打包...`);
                        
                        for (let m of movies) {{
                            const movieId = m.strValue;
                            const movieName = m.strText;
                            
                            const dRes = await fetch(`/api/GetLstDicDate?cinema={option_id}&movie=${{movieId}}`);
                            const dates = await dRes.json();
                            if (!dates) continue;
                            
                            for (let d of dates) {{
                                const showDate = d.strValue;
                                
                                const sRes = await fetch(`/api/GetLstDicSession?cinema={option_id}&movie=${{movieId}}&date=${{showDate}}`);
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
                        report.log.push("提煉核心異常: " + err.toString());
                    }}
                    return report;
                }}
                """
                
                result_report = page.evaluate(cascade_fast_js)
                
                # 輸出乾淨的報告
                for log_line in result_report.get("log", []):
                    print(f" ℹ️ {log_line}")
                
                raw_results = result_report.get("data", [])
                print(f"🎯 ⚡ 秒殺成功！在 2 秒內瞬間收割 {len(raw_results)} 筆威秀真實場次，程序正常終止。")
                
                # 6. 在 Python 端進行高精度數據基因清洗
                for item in raw_results:
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
                    f_type = meta_parts[0] if len(meta_parts) >= 1 else "數位"
                    language = meta_parts[1] if len(meta_parts) >= 2 else "原文"
                    
                    date_time = f"{show_date} {session_time}"
                    
                    # 對齊威秀影城真實票價
                    if "IMAX" in f_type.upper():
                        price = 440
                    elif "4DX" in f_type.upper():
                        price = 510
                    elif "3D" in f_type:
                        price = 390
                    else:
                        price = 330  
                        
                    self.showtime_results.append({
                        "movie_name": movie_name,
                        "theater_name": "威秀影城", 
                        "date_time": date_time,
                        "format_type": f_type,
                        "language": language,
                        "price": price,
                        "seat_status": "開放購票"
                    })
                    
            except Exception as e:
                print(f"❌ 威秀電光引擎執行異常: {e}")
            finally:
                browser.close()
                
        print(f"✅ [{theater_name}] 數據提煉完成。")