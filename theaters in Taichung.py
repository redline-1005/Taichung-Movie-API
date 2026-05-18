# theaters in Taichung
import csv
import re
import os

file_name = '臺中市各電影院名冊.CSV'

# 取得目前這份 .py 檔所在的資料夾路徑
base_dir = os.path.dirname(os.path.abspath(__file__))

# 將資料夾路徑與 CSV 檔名結合
file_path = os.path.join(base_dir, '臺中市各電影院名冊.CSV')

with open(file_name, mode='r', encoding='utf-8-sig') as f:

    taichung_theaters = []
    
    reader = csv.DictReader(f) # 使用 DictReader 自動對應標題
    
    for row in reader:
        
        full_name = row['業者'] # 【清理名稱】從「業者」欄位提取括號內的名字 (例如: 新光影城)
        match = re.search(r'\((.*?)\)', full_name)
        clean_name = match.group(1) if match else full_name
        
        # 提取行政區：從「地址」欄位抓取「...市」到「...區」之間的文字
        address = row['地址']
        district = "未知"
        if "臺中市" in address or "台中市" in address:
            # 簡單抓取：例如 40756臺中市西屯區... 抓出 西屯區
            dist_match = re.search(r'市(.*?[區|市])', address)
            if dist_match:
                district = dist_match.group(1)
        
        clean_address = "未知"
        if "區" in address:
            clean_address_match = re.search(r'區(.*?[號])', address)
            if clean_address_match: 
                clean_address = clean_address_match.group(1)
        
        # 3. 整理存入清單
        taichung_theaters.append({
            "name": clean_name,
            "city": "台中市",
            "district": district,
            "address": clean_address,
            "url": row['網址']
        })

# 檢查前三筆成果
for t in taichung_theaters[:]:
    print(f"影城: {t['name']} | 地區: {t['district']} | 地址：{t['address']} | \n官網: {t['url']}")