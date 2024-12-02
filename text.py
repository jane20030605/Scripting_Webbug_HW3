import requests
import re

# 目標網址
url = "https://ai.ncut.edu.tw/p/412-1063-2382.php"

# 發送 HTTP 請求
response = requests.get(url)

# 確認請求是否成功
if response.status_code == 200:
    # 取得網頁內容
    html_content = response.text

    # 定義正則表達式模式
    name_pattern = r'<a[^>]*class=".*?mtitle.*?"[^>]*>(.*?)</a>'
    email_pattern = r'信箱：</span>([^<]+)</p>'
    ext_pattern = r'分機 ([0-9]+)</p>'

    # 匹配所有姓名、信箱、分機
    names = re.findall(name_pattern, html_content)
    emails = re.findall(email_pattern, html_content)
    exts = re.findall(ext_pattern, html_content)

    # 整理並輸出結果
    for i in range(len(names)):
        name = names[i] if i < len(names) else "N/A"
        email = emails[i] if i < len(emails) else "N/A"
        ext = exts[i] if i < len(exts) else "N/A"
        print(f"姓名: {name}, 信箱: {email}, 分機: {ext}")

else:
    print(f"無法訪問網頁，HTTP 狀態碼: {response.status_code}")
