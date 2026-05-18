# main_scraper.py
from sqlmodel import Session, select
from database import engine
from models import Showtime

# 匯入你寫好的 7 大影城核心爬蟲腳本
from scrapers.in89_scraper import In89Scraper
from scrapers.times_scraper import TimesScraper
from scrapers.sk_scraper import SKScraper
from scrapers.vieshow_scraper import VieshowScraper
from scrapers.showtime_scraper import ShowtimeScraper
from scrapers.chin_chin_scraper import ChinChinScraper
from scrapers.sunrise_scraper import SunriseScraper

def update_all_taichung_showtimes():
    print("\n==================================================")
    print("🎬  開始執行大台中每日場次自動更新程序 (全分店完全體)  🎬")
    print("==================================================")
    
    # 🌟 這裡就是完整的台中影城地圖！再也沒有任何人會被漏掉
    scrapers = {
        # --- 獨立/地方指標影城 ---
        "豐原in89豪華影城": In89Scraper(),
        "清水時代戲院": TimesScraper(),
        "親親大戲院": ChinChinScraper(),
        "日日新大戲院": SunriseScraper(),
        "台中中港新光影城": SKScraper(),
        
        # --- 威秀影城全台中體系 ---
        "台中大遠百威秀影城": VieshowScraper(),
        "台中老虎城威秀影城": VieshowScraper(),       # 迎回老虎城
        "台中大魯閣新時代威秀影城": VieshowScraper(),  # 迎回新時代
        
        # --- 秀泰影城全台中體系 ---
        "台中站前秀泰影城": ShowtimeScraper(),
        "台中文心秀泰影城": ShowtimeScraper(),         # 迎回文心
        "台中麗寶秀泰影城": ShowtimeScraper(),         # 迎回麗寶
    }
    
    with Session(engine) as session:
        # 1. 確保只有在最開始時清空一次資料庫
        print("🧹 正在清空舊放映時刻表...")
        old_slots = session.exec(select(Showtime)).all()
        for slot in old_slots:
            session.delete(slot)
        session.commit()
        print("✅ 舊資料清理完畢。")

        # 2. 依序調度無情機器人前往各分店收割
        for theater_name, scraper_instance in scrapers.items():
            print(f"\n🚀 [開始處理] {theater_name}")
            print("--------------------------------------------------")
            try:
                # 呼叫爬蟲（請確保你的 Vieshow 和 Showtime 爬蟲內部，
                # 有根據傳入的 theater_name 關鍵字去點擊對應的分店網頁或切換 API 參數喔！）
                scraper_instance.fetch_showtimes(theater_name)
                
                for s_data in scraper_instance.showtime_results:
                    s_data['theater_name'] = theater_name 
                    showtime = Showtime(**s_data)
                    session.add(showtime)
                
                session.commit()
                print(f"🎉 {theater_name} 成功同步 {len(scraper_instance.showtime_results)} 筆場次！")
            except Exception as e:
                print(f"❌ {theater_name} 腳本執行失敗。錯誤原因: {e}")
                session.rollback()

    print("\n==================================================")
    print("🏁 大台中所有分店數據全部歸位！API 真正滿血復活！")
    print("==================================================")

if __name__ == "__main__":
    update_all_taichung_showtimes()