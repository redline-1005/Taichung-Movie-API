# init_theaters.py

import csv
import os
from sqlmodel import Session, select
from database import init_db, engine
from models import Theater

def clean_theater_data(file_path):
    """讀取精準的影城 CSV 資料，並對齊 Theater 模型欄位"""
    cleaned_theaters = []
    
    if not os.path.exists(file_path):
        print(f"❌ 錯誤：找不到檔案 {file_path}，請確認檔案是否存在於專案目錄下。")
        return []

    # 使用 utf-8-sig 讀取，完美相容可能包含 BOM 的 CSV 檔案
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 🌟 直接擷取我們量身打造的精準乾淨欄位
            theater_name = row.get('theater_name', '').strip()
            branch = row.get('branch', '').strip()
            city = row.get('city', '台中市').strip()
            district = row.get('district', '未知區').strip()
            url = row.get('url', '').strip()
            
            if theater_name:
                cleaned_theaters.append({
                    "name": theater_name,     # 完美對齊爬蟲與 API 的主名稱
                    "branch": branch,
                    "city": city,
                    "district": district,
                    "url": url
                })
            
    return cleaned_theaters

def initialize_database_with_csv():
    print("\n==================================================")
    print("🎬  開始讀取CSV檔案中影城資料並初始化台中影城資料庫  🎬")
    print("==================================================")
    
    # 建立或檢查資料庫表格
    init_db()
    
    # 🌟 指向我們全新的 11 間影城黃金名冊檔案
    csv_file = "init_theaters.csv"
    theaters_list = clean_theater_data(csv_file)
    
    if not theaters_list:
        print("❌ 沒有讀取到任何影城資料，初始化中斷。")
        return

    with Session(engine) as session:
        # 清除資料庫舊有的影廳清單（避免重複插入或留有舊政府資料的髒資料）
        print("🧹 正在清空舊有影城基本資料清單...")
        existing_theaters = session.exec(select(Theater)).all()
        for t in existing_theaters:
            session.delete(t)
        session.commit()

        # 將清洗完的 11 間大台中影城一次寫入資料庫
        print(f"🚀 成功解析出 {len(theaters_list)} 間大台中核心影城，準備匯入資料庫...")
        for t_data in theaters_list:
            print(f" 💾 [寫入資料庫] 影城: {t_data['name'].ljust(18)} | 區域: {t_data['district']}")
            
            # 使用解包技術安全寫入物件
            theater = Theater(**t_data)
            session.add(theater)
            
        session.commit()
    print("==================================================")
    print("🏁  台中 11 間核心影城基本資料初始化程序完成 ")
    print("==================================================\n")

if __name__ == "__main__":
    initialize_database_with_csv()