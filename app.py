import re
import requests
import sqlite3
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText


def setup_database():
    """
    設定 SQLite 資料庫，創建 contacts 資料表。
    """
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ext TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()


def save_to_database(name: str, ext: str, email: str):
    """
    儲存抓取到的聯絡資訊到資料庫，排除重複資料。
    param name: 姓名
    param ext: 分機
    param email: Email
    """
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO contacts (name, ext, email)
        VALUES (?, ?, ?)
    ''', (name, ext, email))
    conn.commit()
    conn.close()


def scrape_contacts(url: str) -> list[dict]:
    """
    從指定的 URL 抓取聯絡資訊。
    參數: url (str): 網頁的 URL。
    回傳: list[dict]: 包含聯絡資訊的字典列表，每個字典包含 'name', 'ext', 和 'email'。
    """
    try:
        # 設定超時為 10 秒
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 檢查是否為 200 OK
    except requests.Timeout:
        raise RuntimeError("抓取網頁超時，請檢查網絡連接。")
    except requests.RequestException as e:
        raise RuntimeError(f"無法抓取資料: {e}")

    html_content = response.text

    # 假設聯絡人資料包含姓名、分機和 Email，可以用更適合的正則表達式
    pattern = re.compile(
        r'<div.*?>.*?<p>(.*?)</p>.*?<p>(\d{4,})|無分機</p>.*?<p>(\S+@\S+\.\S+)</p>.*?</div>',
        re.DOTALL
    )
    matches = pattern.findall(html_content)

    contacts = []
    for match in matches:
        contacts.append({
            "name": match[0].strip(),
            "ext": match[1].strip() if match[1] else "無分機",
            "email": match[2].strip()
        })

    if not contacts:
        raise RuntimeError("未能從頁面中提取聯絡資訊，請檢查網頁格式。")

    return contacts


def display_contacts(contacts: list[dict]) -> None:
    """
    將聯絡資訊顯示在 Tkinter 視窗中。
    contacts (list[dict]): 包含聯絡資訊的字典列表。
    """
    text_display.delete(1.0, "end")
    if not contacts:
        text_display.insert("end", "沒有抓取到聯絡資訊。\n")
        return

    text_display.insert("end", f"{'姓名':<20}{'分機':<10}{'Email':<30}\n")
    text_display.insert("end", "-" * 60 + "\n")
    for contact in contacts:
        text_display.insert(
            "end", f"{contact['name']:<20}{contact['ext']:<10}{contact['email']:<30}\n"
        )


def fetch_contacts() -> None:
    """
    抓取並顯示聯絡資訊，並將其儲存到資料庫。
    """
    url = url_var.get()
    if not url:
        messagebox.showerror("錯誤", "請輸入有效的 URL。")
        return

    try:
        contacts = scrape_contacts(url)
        display_contacts(contacts)
        # 儲存到資料庫
        for contact in contacts:
            save_to_database(contact['name'], contact['ext'], contact['email'])
        messagebox.showinfo("成功", "聯絡資訊已成功抓取並儲存到資料庫。")
    except RuntimeError as e:
        messagebox.showerror("錯誤", str(e))


# 建立 Tkinter 主視窗
root = Tk()
root.title("聯絡資訊爬蟲")
root.geometry("640x480")

# 網址輸入框
url_var = StringVar(value="https://ai.ncut.edu.tw/p/412-1063-2382.php")
Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = Entry(root, textvariable=url_var, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")

# 抓取按鈕
fetch_button = Button(root, text="抓取", command=fetch_contacts)
fetch_button.grid(row=0, column=2, padx=10, pady=10)

# 顯示區域
text_display = ScrolledText(root, wrap="word", width=80, height=20)
text_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# 設定 grid 權重
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 初始化資料庫
setup_database()

# 啟動主事件循環
root.mainloop()
