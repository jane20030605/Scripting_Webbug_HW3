import requests
import re
import pandas as pd

# 設定目標網頁 URL
url = "https://ai.ncut.edu.tw/p/412-1063-2382.php"  # 替換為你的網頁網址

# 發送 GET 請求獲取網頁內容
response = requests.get(url)

# 確保網頁下載成功
if response.status_code == 200:
    html_content = response.text

    # 使用正則表達式提取資料，假設每條資料包括名稱、信箱、電話
    # 根據你提供的範本，假設HTML中每個人物的資料是以以下格式呈現：
    pattern = re.compile(r'(<li>(.*?)</li>)', re.DOTALL)
    items = re.findall(pattern, html_content)

    # 用來儲存每個人的資料
    data = []

    # 處理每一條資料
    for item in items:
        # 假設每條資料包含：名稱、信箱、電話
        name_pattern = re.search(r'>([^<]+)<', item[1])  # 擷取名字
        email_pattern = re.search(r'信箱：(.*?)(?=<)', item[1])  # 擷取email
        phone_pattern = re.search(r'電話：(.*?)(?=<)', item[1])  # 擷取電話

        if name_pattern and email_pattern and phone_pattern:
            name = name_pattern.group(1).strip()
            email = email_pattern.group(1).strip()
            phone = phone_pattern.group(1).strip()
            data.append([name, email, phone])

    # 使用 pandas 格式化成表格顯示
    df = pd.DataFrame(data, columns=["姓名", "信箱", "電話"])
    print(df)
else:
    print("網頁下載失敗，狀態碼:", response.status_code)
