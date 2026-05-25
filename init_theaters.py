# init_theaters.py
import csv
import os
from sqlmodel import Session, delete
from database import init_db, engine
from models import Theater


def load_theaters_from_csv(file_path):
    if not os.path.exists(file_path):
        print(f"找不到檔案: {file_path}")
        return []

    theaters = []
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            name = row.get('theater_name', '').strip()
            if name:
                theaters.append({
                    "name": name,
                    "branch": row.get('branch', '').strip(),
                    "city": row.get('city', '台中市').strip(),
                    "district": row.get('district', '未知區').strip(),
                    "url": row.get('url', '').strip()
                })
    return theaters


def initialize_database_with_csv():
    init_db()

    theaters = load_theaters_from_csv("init_theaters.csv")
    if not theaters:
        print("未讀取到任何影城資料，初始化中斷")
        return

    with Session(engine) as session:
        session.exec(delete(Theater))
        session.commit()

        for t_data in theaters:
            session.add(Theater(**t_data))
        session.commit()

    print(f"完成，共寫入 {len(theaters)} 間影城")


if __name__ == "__main__":
    initialize_database_with_csv()